import ctypes
import sys
import pymem
import customtkinter
import tkinter
from pymem.exception import ProcessNotFound, MemoryReadError, MemoryWriteError

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

if not is_admin():
    print("Not running as administrator. Re-launching with administrative privileges...")
    ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, ' '.join(sys.argv), None, 1)
    sys.exit()

# Constants for memory protection
PAGE_READWRITE = 0x04
PAGE_WRITECOPY = 0x08
MEM_COMMIT = 0x1000

# MemoryBasicInformation structure
class MEMORY_BASIC_INFORMATION(ctypes.Structure):
    _fields_ = [("BaseAddress", ctypes.c_void_p),
                ("AllocationBase", ctypes.c_void_p),
                ("AllocationProtect", ctypes.c_ulong),
                ("RegionSize", ctypes.c_size_t),
                ("State", ctypes.c_ulong),
                ("Protect", ctypes.c_ulong),
                ("Type", ctypes.c_ulong)]

def query_memory_info(handle, address):
    mbi = MEMORY_BASIC_INFORMATION()
    result = ctypes.windll.kernel32.VirtualQueryEx(handle, ctypes.c_void_p(address), ctypes.byref(mbi), ctypes.sizeof(mbi))
    if result == 0:
        raise MemoryReadError("VirtualQueryEx failed")
    return mbi

def find_writable_memory_region(handle, start_address=0x00000000, end_address=0x7FFFFFFF):
    address = start_address
    while address < end_address:
        try:
            mbi = query_memory_info(handle, address)
            if mbi.Protect in (PAGE_READWRITE, PAGE_WRITECOPY) and mbi.State == MEM_COMMIT:
                return mbi.BaseAddress
            address += mbi.RegionSize
        except MemoryReadError:
            address += 0x1000  # Skip a page
    return None

customtkinter.set_appearance_mode("dark")

app = customtkinter.CTk()
app.configure(bg="black")
app.geometry("700x300")
app.title("NOVA")

label = customtkinter.CTkLabel(master=app, text="MADE BY NOVA", text_color="#FF0000")
label.place(relx=0.5, rely=0.1, anchor=tkinter.CENTER)

entry = customtkinter.CTkEntry(master=app,
                               placeholder_text="process name",
                               width=120,
                               height=25,
                               border_width=2,
                               corner_radius=10)
entry.place(relx=0.5, rely=0.2, anchor=tkinter.CENTER)

entry1 = customtkinter.CTkEntry(master=app,
                               placeholder_text="memory address",
                               width=120,
                               height=25,
                               border_width=2,
                               corner_radius=10)
entry1.place(relx=0.5, rely=0.4, anchor=tkinter.CENTER)

entry2 = customtkinter.CTkEntry(master=app,
                               placeholder_text="length",
                               width=120,
                               height=25,
                               border_width=2,
                               corner_radius=10)
entry2.place(relx=0.5, rely=0.6, anchor=tkinter.CENTER)

def button_event():
    try:
        procname = entry.get()
        address = int(entry1.get(), 0)
        length = int(entry2.get(), 0)

        pm = pymem.Pymem(procname)
        process_id = pm.process_id
        handle = pm.process_handle
        print(f"Process ID: {process_id}, Process Name: {procname}")
        print(f"Memory Address: {address}, Length: {length}")

        value = "." * length  # Create a string of dots with the specified length

        print(f"Writing value: {value}")

        # Attempt to read the memory to check if it's accessible
        try:
            original_value = pm.read_bytes(address, length)
            print(f"Original Value: {original_value}")
        except MemoryReadError as e:
            print(f"Cannot read the specified memory address: {e}. It may be invalid or protected.")
            return

        # Ensure the memory address is writable
        memory_info = query_memory_info(handle, address)
        print(f"Memory Info: BaseAddress={memory_info.BaseAddress}, RegionSize={memory_info.RegionSize}, Protect={memory_info.Protect}")
        if memory_info.Protect not in (PAGE_READWRITE, PAGE_WRITECOPY):
            print("Memory address is not writable. Searching for a writable memory region...")

            writable_address = find_writable_memory_region(handle)
            if writable_address:
                print(f"Found writable memory region at: {writable_address}")
                pm.write_string(writable_address, value)
                print(f"Successfully wrote {value} to writable address {writable_address} in process {procname}")
            else:
                print("No writable memory region found.")
            return

        pm.write_string(address, value)
        print(f"Successfully wrote {value} to address {address} in process {procname}")

    except ProcessNotFound:
        print("Process not found. Please make sure the process name is correct.")
    except MemoryReadError as e:
        print(f"Memory read error: {e}. Please make sure the memory address is correct.")
    except MemoryWriteError as e:
        print(f"Memory write error: {e}. Please make sure the memory address is correct and accessible.")
    except PermissionError:
        print("Permission error. Please run the script as an administrator.")
    except Exception as e:
        print(f"An error occurred: {e}")

button = customtkinter.CTkButton(master=app,
                                 width=120,
                                 height=32,
                                 border_width=0,
                                 corner_radius=8,
                                 fg_color="#FF0000",
                                 hover_color="#6A6767",
                                 text="remove string",
                                 command=button_event)

button.place(relx=0.5, rely=0.8, anchor=tkinter.CENTER)
app.mainloop()
