import pandas as pd
import numpy as np

def get_decoded_data(flip_bit=False):
    ## Read raw data
    df = pd.read_csv("digital.csv")

    data = df.to_numpy()
    ## Convert data into bytes
    bytes = np.zeros(shape=(df.shape[0], 2), dtype=np.uint8)

    kMaxBits = int(8)
    kClockTime = 0.000002
    kTol = 0.0000002

    bit_count = int(0)
    mosi_byte = int(0)
    miso_byte = int(0)

    kTimeBitIdx = 0
    kMisoBitIdx = 1
    kMosiBitIdx = 2
    kSckBitIdx = 3

    kMisoByteIdx = 0
    kMosiByteIdx = 1

    byte_idx = 0

    print("Decoding...")

    bad_sck = 0
    bad_sck_time = []
    curr_time = 0
    prev_time = 0

    curr_byte_time = 0
    byte_time = []

    for i in range(1, data.shape[0]):
        # Hack to avoid a patch of bad clock cycles that messup the counting (；￣Д￣）
        if data[i][kTimeBitIdx] > 409.379394400 and data[i][kTimeBitIdx] < 409.866634400:
            continue
        
        if((data[i-1][kSckBitIdx] == 0) and (data[i][kSckBitIdx] == 1)):
            curr_time = data[i][kTimeBitIdx]
            dt = (curr_time-prev_time)
            prev_time = curr_time

            shift = (kMaxBits - 1) - bit_count

            # Assume the first bit is good
            if (bit_count == 0):
                curr_byte_time = curr_time
                miso_byte = miso_byte | (int(data[i][kMisoBitIdx]) << shift)
                mosi_byte = mosi_byte | (int(data[i][kMosiBitIdx]) << shift)
                bit_count += 1
            # If clock rate is ok, store the bit
            elif (abs(dt - kClockTime) < kTol):
                miso_byte = miso_byte | (int(data[i][kMisoBitIdx]) << shift)
                mosi_byte = mosi_byte | (int(data[i][kMosiBitIdx]) << shift)
                bit_count += 1
            # If clock rate is bad, reset the byte and store the latest bit in case it's a good bit
            else:
                bad_sck += 1
                bad_sck_time.append(curr_time)
                
                bit_count = 0
                mosi_byte = 0
                miso_byte = 0

                curr_byte_time = curr_time
                miso_byte = miso_byte | (int(data[i][kMisoBitIdx]) << shift)
                mosi_byte = mosi_byte | (int(data[i][kMosiBitIdx]) << shift)
                bit_count += 1

            # We have a full byte. Store and reset counters
            if (bit_count == 8):
                byte_time.append(curr_time)
                bytes[byte_idx][kMisoByteIdx] = miso_byte
                bytes[byte_idx][kMosiByteIdx] = mosi_byte
                byte_idx += 1
                bit_count = 0
                mosi_byte = 0
                miso_byte = 0
        if i % 1000000 == 0:
            print(f'{(i/data.shape[0])*100:.2f}', "%")

    print("100.0 %")
    print("\nBad edges: ", bad_sck)
        
    kValuesEndIdx = byte_idx

    ## Separate by transactions
    transactions = []
    transaction_time = []
    kTransactionSizes = np.array([12, 4, 12, 12, 4, 12, 12, 12, 12, 12])

    size_idx = 0
    j = 0

    while j < kValuesEndIdx:
        tran = np.zeros(kTransactionSizes[size_idx])

        for k in range(0, kTransactionSizes[size_idx]):
            tran[k] = bytes[j + k][kMisoByteIdx]

        transaction_time.append(byte_time[j])
        transactions.append(tran)

        j += kTransactionSizes[size_idx]
        
        if size_idx + 1 == kTransactionSizes.size:
            size_idx = 0
        else:
            size_idx += 1

    ## Get Cell Voltage Groups and their expected PEC value
    counter = 0

    data2pec = []
    pec = []

    for t in transactions:
        if (counter % 10 >= 5) and (counter % 10 <= 8):
            data2pec.append([t[4],t[5],t[6],t[7],t[8],t[9]])
            pec.append(((int(t[10]) << 8 ) | int(t[11])))
        
        counter += 1

    ## Generate PEC15 table
    pec15table = np.zeros(256, dtype=np.int16)
    crc15_poly = int(0x4599)

    remainder = int(0)
    r = int(0)

    for idx in range(0, 256):
        remainder = r << 7
        r += 1

        for j in range(8, 0, -1):
            if (remainder & 0x4000):
                remainder = ((remainder << 1))
                remainder = (remainder ^ crc15_poly)
            else:
                remainder = ((remainder << 1))
        
        pec15table[idx] = np.array(remainder & 0xFFFF).astype(np.uint16)

    ## Calculate PEC
    local_pec = []

    for d in data2pec:
        remainder = np.uint16(0)
        remainder = 16 # PEC seed
        for i in range(0, len(d)):
            address = ((remainder >> 7) ^ np.uint16(d[i])) & 0xFF
            remainder = (remainder << 8) ^ pec15table[address]

        local_pec.append(np.array(remainder * 2).astype(np.uint16))

    ## Compare local to received PEC
    pec_ok = []
    num_success_pec = 0

    for i in range(0, len(pec)):
        pec_ok.append((pec[i] == local_pec[i]))
        if(pec[i] == local_pec[i]):
            num_success_pec += 1

    print("Total", num_success_pec, "successful PEC checks --", f'{(num_success_pec/len(pec)*100):.3f}', "%")

    ## Get all cell voltages
    cell_v = np.zeros((int(len(data2pec)/4), 12), dtype=np.uint16)
    cell_times = np.zeros((int(len(data2pec)/4)*12))

    # get cell times
    counter = 0
    for i in range(0, len(transactions)):
        if (i % 10 == 4) or (i % 10 == 6) or (i % 10 == 8):
            cell_times[counter] = transaction_time[i]
            counter += 1
    cell_times = np.reshape(cell_times, cell_v.shape)

    point_count = 0
    cell_count = 0
    for d in data2pec:
        n = 0
        while n < len(d):
            cell_v[point_count][cell_count] = (int(d[n+1]) << 8) | int(d[n])
            
            if flip_bit and ((int(d[n+1]) << 8) | int(d[n])) > 50000:
                cell_v[point_count][cell_count] = ((int(d[n+1]) << 8) | int(d[n])) & 0x7FFF

            n += 2
            cell_count += 1
        
        if (cell_count == 12):
            cell_count = 0
            point_count += 1

    return (bytes,transactions,transaction_time,data2pec,pec,local_pec,pec_ok,cell_v,cell_times)