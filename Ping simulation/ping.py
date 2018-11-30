#-*- coding:utf-8 -*-
import sys
import socket
import os 
import time
import struct
import select
import random
import string

timeout = 1
count = 5
packetsize = 56



def generate_random_str(randomlength):
    '''
    Randomly generated string
    '''
    str_list = [random.choice(string.digits + string.ascii_letters) for i in range(randomlength)]
    random_str = ''.join(str_list)
    return random_str


def cal_chesksum(icmp):
    '''
    Calculate the checksum 
    '''
    sum = 0
    max_count = (len(icmp)/2)*2

    #add every two bytes (16 bits) (binary summation) until the end result, if there is one byte left, continue to add the previous result
    for i in range(0,max_count,2):
        val = (ord(icmp[i + 1]) << 8) + ord(icmp[i])
        sum = sum + val
        sum = sum & 0xffffffff 


    if max_count<len(icmp):
        sum = sum + ord(icmp[-1])
        sum = sum & 0xffffffff 
    
    #add the upper 16 bits to the lower 16 bits until the upper 16 bits are 0
    sum = (sum >> 16)  +  (sum & 0xffff)
    sum = sum + (sum >> 16)


    ICMP_checksum = ~sum & 0xffff

    #Host byte to network byte sequence
    ICMP_checksum = ICMP_checksum >> 8 | (ICMP_checksum << 8 & 0xff00)
    
    return ICMP_checksum


def send_ping(my_socket,my_ID,target,seq):
    '''
    send ping data to target host
    '''

    target_host = socket.gethostbyname(target)

    #create checksum:0 ICMP header
    #b:char 1, H:unsigned short 2
    ICMP_header = struct.pack('bbHHH',8,0,0,my_ID,seq)
    header_byte = struct.calcsize("d") # sizeof(ICMP_header) = 8
    data = generate_random_str(packetsize)
    ICMP = ICMP_header + data

    #Calculate the checksum 
    ICMP_chesksum = cal_chesksum(ICMP)
    ICMP_header = struct.pack('bbHHH',8,0,socket.htons(ICMP_chesksum),my_ID,seq)
    ICMP = ICMP_header + data

    #send ping
    send_time = time.time()
    my_socket.sendto(ICMP,(target_host,80))

    return send_time


def receive_ping(my_socket,target_host,send_time,timeout):
    '''
    receive ping
    '''
    while True:
        readable = select.select([my_socket], [], [], timeout)
        if readable[0] == []: # Timeout
            return None


        receive_time = time.time()
        recv_ping,addr = my_socket.recvfrom(1024)

        #ping_header = 20 bytes
        ICMP_header = recv_ping[20:28]

        #time to live
        ttl = ord(recv_ping[8])
        
        Type,Code,Checksum,Id,Seq = struct.unpack('bbHHH',ICMP_header)

        if Id == target_host:
            return (receive_time - send_time) * 1000,ttl



def ping_once(seq,target):

    #construct a Socket
    icmp = socket.getprotobyname('icmp')
    my_socket = socket.socket(socket.AF_INET, socket.SOCK_RAW, icmp)

    my_ID = os.getpid() & 0xFFFF #get host ip

    send_time = send_ping(my_socket,my_ID,target,seq)
    delay,ttl = receive_ping(my_socket,my_ID,send_time,timeout)

    if delay  ==  None:
                return

    print '{} bytes from {}: icmp_seq={} ttl={} time={} ms'.format(packetsize+8,target,seq,ttl,str(delay)[:4])
    return delay


def menu():
    global count
    global packetsize
    cmd = sys.argv
    argc = len(cmd)

    if argc == 1 :
        print 'Usage: sudo python ping.py [-c count] [-s packetsize] destination'
        exit()

    if '-h' in cmd :
        print 'Usage: sudo python ping.py [-c count] [-s packetsize] destination'
        exit()

    if '-c' in cmd :
        try:
            count = int(cmd[cmd.index('-c')+1])
        except Exception as e:
            print '''ping.py: option requires an argument -- 'c'\nUsage: python ping.py [-c count] [-s packetsize] destination'''  

    if '-s' in cmd :
        try:
            packetsize = int(cmd[cmd.index('-s')+1])
        except Exception as e:
            print '''ping.py: option requires an argument -- 's'\nUsage: python ping.py [-c count] [-s packetsize] destination'''

    target = cmd[-1]

    ping(target)



def ping(target):
    
    flag_list = []
    success_times = 0
    loss_time = 0

    print 'PING {} {}({}) bytes of data.'.format(target,packetsize,packetsize+8+20)
    start_time = time.time()
    for i in range(1,count+1):
        flag = ping_once(i,target)
        if flag == None:
            flag_list.append(0)
        else:
            flag_list.append(1)

    end_time = time.time()
    all_cost_time = str((end_time - start_time) * 1000).split('.')[0]
    for i in flag_list:
        if i:
            success_times += 1
        else:
            loss_time += 1

    success_percent = (loss_time / count) * 100
    print '\n--- {} ping statistics ---'.format(target)
    print '{} packets transmitted, {} received, {}% packet loss, time {}ms'.format(count,success_times,success_percent,all_cost_time)




if __name__ == '__main__':
    menu()