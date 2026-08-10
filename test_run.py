import sys
from openloader import MainWindow, QApplication
import traceback
import io

app = QApplication(sys.argv)
try:
    print("Creating MainWindow...")
    window = MainWindow()
    print("MainWindow created successfully!")
    window.show()
    print("MainWindow shown!")
    sys.exit(0)
except Exception as e:
    print("Exception during init:")
    traceback.print_exc()
