from typing import List
import os

# Windows imports
import winreg
import win32security
import win32api

# Enable UAC privilege
priv_flags = win32security.TOKEN_ADJUST_PRIVILEGES | win32security.TOKEN_QUERY
hToken = win32security.OpenProcessToken (win32api.GetCurrentProcess (), priv_flags)
privilege_id = win32security.LookupPrivilegeValue (None, "SeBackupPrivilege")
delete_privilege_id = win32security.LookupPrivilegeValue (None, "SeRestorePrivilege")
win32security.AdjustTokenPrivileges (hToken, 0, [(privilege_id, win32security.SE_PRIVILEGE_ENABLED)])
win32security.AdjustTokenPrivileges (hToken, 0, [(delete_privilege_id, win32security.SE_PRIVILEGE_ENABLED)])

# Installed product data
class Product:
    key: any
    package_code: str
    
    # These are just used for prints and aren't needed by the script
    name: str
    version: int
    
    def __init__(self, key, name, package_code, version):
        self.key = key
        self.package_code = package_code
        
        self.name = name
        self.version = version

# All found installed products
products: List[Product] = []

# Change this if you want to scan for more than 1024 products
MAX_INSTALLED_PRODUCTS = 1024

# Query Registry keys in "HKEY_LOCAL_MACHINE\SOFTWARE\Classes\Installer\Products"
key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\\Classes\\Installer\\Products")
for i in range(MAX_INSTALLED_PRODUCTS):
    try:
        subkey = winreg.EnumKey(key, i)
        subkey = winreg.OpenKey(key, subkey)
        
        product_name = winreg.QueryValueEx(subkey, "ProductName")
        package_code = winreg.QueryValueEx(subkey, "PackageCode")
        version = winreg.QueryValueEx(subkey, "Version")
        
        # Format as a GUID for easier MSI file lookup
        guid = f"{{{package_code[0][:8]}-{package_code[0][8:12]}-{package_code[0][12:16]}-{package_code[0][16:20]}-{package_code[0][20:]}}}"
        
        # Append to the list
        products.append(Product(subkey, product_name[0], guid, version[0]))
    except:
        break # No more keys
    
# Deletes all sub-keys of a registry key
# Needed because a registry key can't be deleted if it has sub-keys
def delete_sub_key(root, sub):
    try:
        open_key = winreg.OpenKey(root, sub, 0, winreg.KEY_ALL_ACCESS)
        num, _, _ = winreg.QueryInfoKey(open_key)
        for _ in range(num):
            child = winreg.EnumKey(open_key, 0)
            delete_sub_key(open_key, child)
        try:
            winreg.DeleteKey(open_key, '')
        except Exception:
            # log deletion failure
            print(f"Failed to delete {sub}")
        finally:
            winreg.CloseKey(open_key)
    except Exception:
        # log opening/closure failure
        print(f"Failed to open {sub}")

            
# Infinite loop
while True:
    # Clear the console
    print("\033[H\033[J")
    
    # Search for a product
    query = input("Search for a product: ").strip()
    if query == "":
        break
    
    found = False
    found_products = []
    for product in products:
        if query.lower() in product.name.lower():
            print(f"{product.name} ({product.version}) - {product.package_code}")
            found = True
            found_products.append(product)
        
    # Log all of the not-found products
    # These are products that are in the registry but not in "C:\Windows\Installer"
    # **This** is the situation that leads to the annoying "Network resource unavailable" error
    not_found = []
    for product in found_products:
        # Get version as hex string
        version = hex(product.version)[2:]
        
        # Check if installer is present in "C:\Windows\Installer"
        try:
            user_temp_dir = os.environ["TEMP"]
            
            files = [
                f"C:\\Windows\\Installer\\{product.package_code}\\{version}.msi",
                f"{user_temp_dir}\\{product.package_code}\\{version}.msi"
            ]
            
            for file in files:
                if os.path.exists(file):
                    # Check if it's **actually** an MSI file
                    with open(file, "rb") as f:
                        magic = f.read(4)
                        if magic != b"\xD0\xCF\x11\xE0":
                            not_found.append(product) # caught ya
                        else:
                            found = True
                            break
                else:
                    not_found.append(product)
                    break
        except: # Shouldn't really happen, but just in case
            not_found.append(product)
        
    # If there are any not-found products, offer to delete them
    if len(not_found) > 0:
        print("\n*** Products not found: ***")
        for product in not_found:
            print(f"{product.name} ({product.version}) - {product.package_code}")
            
        delete = input("Delete these products from the registry? (y/n) ").strip().lower()
        
        if delete == "y":
            for product in not_found:
                # Backup the key under `./uninstalled/{product.package_code}.reg`
                file = f"./uninstalled/{product.package_code}.reg"
                if os.path.exists(file):
                    os.remove(file)
                    
                print(f"Backing up {product.name} ({product.version}) - {product.package_code} to {file}")
                try:
                    winreg.SaveKey(product.key, file)
                except OSError:
                    print("WARNING: Failed to save key backup! Skipping...")
                    continue
                
                # Delete subkeys and key
                print(f"Deleting {product.name} ({product.version}) - {product.package_code}")
                delete_sub_key(product.key, '')
                
                # This shouldn't be needed but we want to make sure it's *really* gone
                try:
                    winreg.DeleteKey(product.key, "")
                except OSError:
                    continue
    
    if not found:
        print("No products found.")
    
    # Wait until going back to the search prompt (so the user can read the output before it gets cleared)
    input("Press Enter to continue...")