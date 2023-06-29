for i in range(1, data.shape[0]):
    if((data[i-1][kSckBitIdx] == 0) and (data[i][kSckBitIdx] == 1)):
        curr_time = data[i][kTimeBitIdx]
        dt = (curr_time-prev_time)
        prev_time = curr_time
        if ((dt < 0.000001)
            or ((dt > 0.000100) and (dt < 0.005))):
            bad_sck += 1
            bad_sck_time.append(curr_time)
            
            if bit_count < 7:
                continue
            
            bit_count = 7
            mosi_byte = 0
            miso_byte = 0
            continue

        miso_byte = miso_byte | (int(data[i][kMisoBitIdx]) << bit_count)
        mosi_byte = mosi_byte | (int(data[i][kMosiBitIdx]) << bit_count)

        if (curr_time > 7.445410300):
            g = 0

        bit_count = bit_count - 1

        if (bit_count < 0):
            bytes[byte_idx][kMisoByteIdx] = miso_byte
            bytes[byte_idx][kMosiByteIdx] = mosi_byte
            byte_idx += 1
            bit_count = 7
            mosi_byte = 0
            miso_byte = 0
    if i % 1000000 == 0:
        print(f'{(i/data.shape[0])*100:.2f}', "%")