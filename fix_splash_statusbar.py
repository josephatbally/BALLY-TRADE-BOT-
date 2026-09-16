with open(r"mobile\src\screens\SplashScreen.tsx", "r", encoding="utf-8") as f:
    content = f.read()

# Remove backgroundColor from StatusBar JSX
content = content.replace(
    '<StatusBar barStyle="light-content" backgroundColor="#05070D" />',
    '<StatusBar barStyle="light-content" />'
)

with open(r"mobile\src\screens\SplashScreen.tsx", "w", encoding="utf-8") as f:
    f.write(content)

print("SUCCESS: SplashScreen.tsx updated")
