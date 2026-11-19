from pwdlib import PasswordHash

password_hash = PasswordHash.recommended()

print("Hash de admin123:")
print(password_hash.hash("admin123"))

print("\nHash de farm123:")
print(password_hash.hash("farm123"))