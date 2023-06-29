/******************************************************************************

                              Online C++ Compiler.
               Code, Compile, Run and Debug C++ program online.
Write your code in this editor and press "Run" button to compile and execute it.

*******************************************************************************/

#include <iostream>
#include <cstdint>

#include "table.h"

using namespace std;

int16_t pec15Table[256];
int16_t CRC15_poly = 0x4599;

uint16_t pec15(char *data, int len)
{
    int16_t remainder, address;
    remainder = 16;  // PEC seed
    for (int i = 0; i < len; i++)
    {
        address = ((remainder >> 7) ^ data[i]) & 0xFF;  // Calculate PEC table address
        remainder = (remainder << 8) ^ pec15Table[address];
    }
    return (remainder * 2);  // The CRC15 has a 0 in the LSB so the final value
                             // must be multiplied by 2
}

int main()
{
    int16_t remainder;
    for (int i = 0; i < 256; i++)
    {
        remainder = i << 7;
        for (int bit = 8; bit > 0; --bit)
        {
            if (remainder & 0x4000)
            {
                remainder = ((remainder << 1));
                remainder = (remainder ^ CRC15_poly);
            }
            else
            {
                remainder = ((remainder << 1));
            }
        }
        pec15Table[i] = remainder & 0xFFFF;
    }
    
    for (int i{0}; i < 20; i++)
    {
        printf("%i\n", pec15((char*)(arr[i]), 6));
    }

    return 0;
}
