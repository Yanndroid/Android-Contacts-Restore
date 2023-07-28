import sqlite3

INPUT_DATABASE = "databases/contacts2.db"
OUTPUT_VCF = "contacts.vcf"


def text_to_bytes(text):
    return f"={bytes(text, 'utf-8').hex('=')}"


class NameInfo:
    def __init__(self, data):
        self.full_name = data["data1"] if data["data1"] else ""
        self.first_name = data["data2"] if data["data2"] else ""
        self.last_name = data["data3"] if data["data3"] else ""
        self.prefix_name = data["data4"] if data["data4"] else ""
        self.middle_name = data["data5"] if data["data5"] else ""
        self.suffix_name = data["data6"] if data["data6"] else ""

    def __str__(self):
        return f"N:{self.last_name};{self.first_name};{self.middle_name};{self.prefix_name};{self.suffix_name}\nFN:{self.full_name}"


class EventInfo:
    TYPE_CUSTOM = 0
    TYPE_ANNIVERSARY = 1
    TYPE_OTHER = 2
    TYPE_BDAY = 3

    def __init__(self, data):
        self.event_date = data["data1"]
        self.event_type = data["data2"]
        self.event_label = data["data3"] if data["data3"] else ""

    def __str__(self):
        if self.event_type == self.TYPE_BDAY:
            return f"BDAY:{self.event_date}"
        else:
            return f"X-ANDROID-CUSTOM:vnd.android.cursor.item/contact_event;{self.event_date};{self.event_type};{self.event_label};;;;;;;;;;;;0"


class EmailInfo:
    TYPE_CUSTOM = 0
    TYPE_HOME = 1
    TYPE_WORK = 2
    TYPE_OTHER = 3

    def __init__(self, data):
        self.email = data["data1"]
        self.email_type = data["data2"]
        self.email_label = data["data3"] if data["data3"] else ""

    def type_name(self):
        if self.email_type == self.TYPE_CUSTOM: return f";X-{self.email_label}"
        if self.email_type == self.TYPE_HOME: return ";HOME"
        if self.email_type == self.TYPE_WORK: return ";WORK"
        if self.email_type == self.TYPE_OTHER: return ""
        return ""

    def __str__(self):
        return f"EMAIL{self.type_name()}:{self.email}"


class PhoneInfo:
    TYPE_CUSTOM = 0
    TYPE_HOME = 1
    TYPE_MOBILE = 2
    TYPE_WORK = 3
    TYPE_FAX_WORK = 4
    TYPE_FAX_HOME = 5
    TYPE_PAGER = 6
    TYPE_VOICE = 7
    TYPE_CALLBACK = 8

    def __init__(self, data):
        self.phone_number = data["data1"].replace(" ", "")
        self.phone_type = data["data2"]
        self.phone_label = data["data3"] if data["data3"] else ""

    def type_name(self):
        if self.phone_type == self.TYPE_CUSTOM: return f";X-{self.phone_label}"
        if self.phone_type == self.TYPE_HOME: return ";HOME"
        if self.phone_type == self.TYPE_MOBILE: return ";CELL"
        if self.phone_type == self.TYPE_WORK: return ";WORK"
        if self.phone_type == self.TYPE_FAX_WORK: return ";WORK;FAX"
        if self.phone_type == self.TYPE_FAX_HOME: return ";HOME;FAX"
        if self.phone_type == self.TYPE_PAGER: return ";PAGER"
        if self.phone_type == self.TYPE_VOICE: return ";VOICE"
        if self.phone_type == self.TYPE_CALLBACK: return ";CALLBACK"
        return ""

    def __str__(self):
        return f"TEL{self.type_name()}:{self.phone_number}"


class AddressInfo:
    TYPE_CUSTOM = 0
    TYPE_HOME = 1
    TYPE_WORK = 2
    TYPE_OTHER = 3

    def __init__(self, data):
        self.address_full = data["data1"] if data["data1"] else ""
        self.address_type = data["data2"]
        self.address_label = data["data3"] if data["data3"] else ""
        self.street = data["data4"] if data["data4"] else ""
        self.city = data["data7"] if data["data7"] else ""
        self.state = data["data8"] if data["data8"] else ""
        self.zip = data["data9"] if data["data9"] else ""
        self.country = data["data10"] if data["data10"] else ""

    def type_name(self):
        if self.address_type == self.TYPE_CUSTOM: return f";X-{self.address_label}"
        if self.address_type == self.TYPE_HOME: return ";HOME"
        if self.address_type == self.TYPE_WORK: return ";WORK"
        if self.address_type == self.TYPE_OTHER: return ""
        return ""

    def __str__(self):
        return f"ADR{self.type_name()};CHARSET=UTF-8;ENCODING=QUOTED-PRINTABLE:;;{text_to_bytes(self.street)};{text_to_bytes(self.city)};{text_to_bytes(self.state)};{text_to_bytes(self.zip)};{text_to_bytes(self.country)}"


class NoteInfo:
    def __init__(self, data):
        self.note = data["data1"] if data["data1"] else ""

    def __str__(self):
        return f"NOTE;ENCODING=QUOTED-PRINTABLE:{text_to_bytes(self.note)}"


class Contact:
    def __init__(self):
        self.name = None
        self.event = []
        self.email = []
        self.phone = []
        self.address = []
        self.note = None

    def __str__(self):
        vCard = "BEGIN:VCARD\nVERSION:2.1\n"
        vCard += str(self.name) + "\n"
        for p in self.phone: vCard += str(p) + "\n"
        for e in self.email: vCard += str(e) + "\n"
        for a in self.address: vCard += str(a) + "\n"
        for e in self.event: vCard += str(e) + "\n"
        if self.note: vCard += str(self.note) + "\n"
        vCard += "END:VCARD\n"
        return vCard


def main():
    contacts = {}

    conn = sqlite3.connect(INPUT_DATABASE)
    conn.create_collation("PHONEBOOK", lambda x, y: 0)
    conn.row_factory = sqlite3.Row

    raw_data = conn.execute("SELECT * FROM view_data").fetchall()

    conn.commit()
    conn.close()

    for row in raw_data:
        if row["account_type"] != "com.osp.app.signin": continue

        id = row["lookup"]
        if id not in contacts: contacts[id] = Contact()

        if row["mimetype"] == "vnd.android.cursor.item/name":
            contacts[id].name = NameInfo(row)
            continue

        if row["mimetype"] == "vnd.android.cursor.item/contact_event":
            contacts[id].event.append(EventInfo(row))
            continue

        if row["mimetype"] == "vnd.android.cursor.item/email_v2":
            contacts[id].email.append(EmailInfo(row))
            continue

        if row["mimetype"] == "vnd.android.cursor.item/phone_v2":
            contacts[id].phone.append(PhoneInfo(row))
            continue

        if row["mimetype"] == "vnd.android.cursor.item/postal-address_v2":
            contacts[id].address.append(AddressInfo(row))
            continue

        if row["mimetype"] == "vnd.android.cursor.item/note":
            contacts[id].note = NoteInfo(row)
            continue

    with open(OUTPUT_VCF, 'w') as f:
        for c in contacts.values():
            f.write(str(c))


if __name__ == '__main__':
    main()
