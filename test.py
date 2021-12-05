from miio import Vacuum
import time

IP_ADDR = "192.168.100.185"
TOKEN   = "6c3116373a61676b342a6a3313546260"

print("Roborock Remote test script")
vac = Vacuum(IP_ADDR, TOKEN)
print(vac.segment_clean([6]))
time.sleep(5)
print(vac.status())
print(vac.get_room_mapping())
print(vac.get_segment_status())