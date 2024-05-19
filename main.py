from pyicloud import PyiCloudService
import sys, os, json
from datetime import datetime

api = PyiCloudService('enter email', 'enter password')

if api.requires_2fa:
    print("Two-factor authentication required.")
    code = input("Enter the code you received of one of your approved devices: ")
    result = api.validate_2fa_code(code)
    print("Code validation result: %s" % result)

    if not result:
        print("Failed to verify security code")
        sys.exit(1)

    if not api.is_trusted_session:
        print("Session is not trusted. Requesting trust...")
        result = api.trust_session()
        print("Session trust result %s" % result)

        if not result:
            print("Failed to request trust. You will likely be prompted for the code again in the coming weeks")
elif api.requires_2sa:
    import click
    print("Two-step authentication required. Your trusted devices are:")

    devices = api.trusted_devices
    for i, device in enumerate(devices):
        print(
            "  %s: %s" % (i, device.get('deviceName',
            "SMS to %s" % device.get('phoneNumber')))
        )

    device = click.prompt('Which device would you like to use?', default=0)
    device = devices[device]
    if not api.send_verification_code(device):
        print("Failed to send verification code")
        sys.exit(1)

    code = click.prompt('Please enter validation code')
    if not api.validate_verification_code(device, code):
        print("Failed to verify verification code")
        sys.exit(1)



date_counter = {}
count = 0

counter_file = 'date_counter.json'
base_dir = "D:\\Picture Archives\\Photos_Named"

def load_data(file_path):
    if os.path.exists(file_path):
        if os.path.getsize(file_path) > 0:
            with open(file_path, 'r') as file:
                return json.load(file)
    return {"date_counter": {}, "breakpoint": 0}

data = load_data(counter_file)
date_counter = data.get("date_counter", {})
breakpoint = data.get("breakpoint", 0)

# print(date_counter)
# print(breakpoint)


if not os.path.exists(base_dir):
    os.makedirs(base_dir)

for photo in api.photos.all:
    count += 1

    if count <= data["breakpoint"]: #4804
        print(f"{count} - skipped")
        continue

    photo_date = photo.added_date
    year = photo_date.strftime("%Y")
    month = photo_date.strftime("%B")

    year_dir = os.path.join(base_dir, year)
    month_dir = os.path.join(year_dir, month)

    if not os.path.exists(year_dir):
        os.makedirs(year_dir)
    if not os.path.exists(month_dir):
        os.makedirs(month_dir)

    photo_date = photo.added_date.strftime('%Y.%m.%d')

    if photo_date in date_counter:
        date_counter[photo_date] += 1
    else:
        date_counter[photo_date] = 1

    file_extension = os.path.splitext(photo.filename)[1]

    new_file_name = f"{photo_date} - {date_counter[photo_date]}{file_extension}"

    new_file_path = os.path.join(month_dir, new_file_name)

    download = photo.download()
    with open(new_file_path, 'wb') as opened_file:
        opened_file.write(download.raw.read())
    
    data["date_counter"] = date_counter

    if (count >= data["breakpoint"]):
        data["breakpoint"] = count

    with open(counter_file, 'w') as file:
        json.dump(data, file)

    print(f"{count} - {new_file_name}")
    