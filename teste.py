from pathlib import Path, PosixPath, PurePath

cwd = Path.cwd()

filename = 'TARIFA_NOVA'
backupname = 'BACKUP_SEGURANCA_TARIFA_ATUAL'

file = PurePath(f"{cwd}/{filename}")
backup = PurePath(f"{cwd}/{backupname}")

print(cwd)
print(Path( __file__ ).absolute())
print(file)
print(backup)



print()