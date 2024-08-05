emulator -avd Pixel_4a_Edited_API_33 -writable-system
adb root
adb shell whoami
adb remount
adb push /Users/batu/Desktop/project_dal/tcpdump /system/xbin/tcpdump
adb shell chmod 6755 /system/xbin/tcpdump
sudo tcpdump -i any -s 0 -w /Users/batu/Desktop/project_dal/slack.pcap

