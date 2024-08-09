emulator -avd Pixel_4a_Edited_API_33 -writable-system
adb root
adb shell whoami
adb remount
adb shell chmod 6755 /system/xbin/tcpdump
adb shell /system/xbin/tcpdump -i any -s 0 -w /sdcard/imas_all_tcpdump.pcap


