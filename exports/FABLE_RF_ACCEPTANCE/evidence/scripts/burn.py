import time, sys
end = time.time() + float(sys.argv[1])
x = 0
while time.time() < end:
    x = (x * 1103515245 + 12345) % 2147483648
