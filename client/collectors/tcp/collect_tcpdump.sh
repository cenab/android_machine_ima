emulator -avd Pixel_4a_Edited_API_33 -writable-system
emulator -avd test_avd -no-window -no-snapshot -wipe-data -accel off
adb root
adb shell whoami
adb remount
adb shell chmod 6755 /system/xbin/tcpdump
adb shell /system/xbin/tcpdump -i any -s 0 -w /sdcard/imas_all_tcpdump.pcap


