adb shell monkey -p org.telegram.messenger.web -c android.intent.category.LAUNCHER 1


start_messaging adb shell input tap 525 1932
type phone number > adb shell input text "5064369339"

adb shell input keycombination 113 29 && adb shell input keyevent 67

#voip based phone numbers are not accepted