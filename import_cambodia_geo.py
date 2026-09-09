"""
Import and manage Cambodia Administrative Locations (2025)
Provinces (25), Districts (210), Communes (1,661) from CambodiaCommuneList2025.csv
"""

import os
import csv
from models import db, Province, District, Commune


PROVINCES_DATA = {
    "01": ("ខេត្តបន្ទាយមានជ័យ", "Banteay Meanchey"),
    "02": ("ខេត្តបាត់ដំបង", "Battambang"),
    "03": ("ខេត្តកំពង់ចាម", "Kampong Cham"),
    "04": ("ខេត្តកំពង់ឆ្នាំង", "Kampong Chhnang"),
    "05": ("ខេត្តកំពង់ស្ពឺ", "Kampong Speu"),
    "06": ("ខេត្តកំពង់ធំ", "Kampong Thom"),
    "07": ("ខេត្តកំពត", "Kampot"),
    "08": ("ខេត្តកណ្តាល", "Kandal"),
    "09": ("ខេត្តកោះកុង", "Koh Kong"),
    "10": ("ខេត្តក្រចេះ", "Kratie"),
    "11": ("ខេត្តមណ្ឌលគិរី", "Mondulkiri"),
    "12": ("រាជធានីភ្នំពេញ", "Phnom Penh"),
    "13": ("ខេត្តព្រះវិហារ", "Preah Vihear"),
    "14": ("ខេត្តព្រៃវែង", "Prey Veng"),
    "15": ("ខេត្តពោធិ៍សាត់", "Pursat"),
    "16": ("ខេត្តរតនគិរី", "Ratanakiri"),
    "17": ("ខេត្តសៀមរាប", "Siem Reap"),
    "18": ("ខេត្តព្រះសីហនុ", "Preah Sihanouk"),
    "19": ("ខេត្តស្ទឹងត្រែង", "Stung Treng"),
    "20": ("ខេត្តស្វាយរៀង", "Svay Rieng"),
    "21": ("ខេត្តតាកែវ", "Takeo"),
    "22": ("ខេត្តឧត្តរមានជ័យ", "Oddar Meanchey"),
    "23": ("ខេត្តកែប", "Kep"),
    "24": ("ខេត្តប៉ៃលិន", "Pailin"),
    "25": ("ខេត្តត្បូងឃ្មុំ", "Tboung Khmum")
}

DISTRICTS_DATA = {
    # 01 Banteay Meanchey
    "0102": ("ស្រុកមង្គលបូរី", "Mongkol Borei"),
    "0103": ("ស្រុកភ្នំស្រុក", "Phnum Srok"),
    "0104": ("ស្រុកព្រះនេត្រព្រះ", "Preah Netr Preah"),
    "0105": ("ស្រុកអូរជ្រៅ", "Ou Chrov"),
    "0106": ("ក្រុងសិរីសោភ័ណ", "Serei Saophoan"),
    "0107": ("ស្រុកថ្មពួក", "Thma Puok"),
    "0108": ("ស្រុកស្វាយចេក", "Svay Chek"),
    "0109": ("ស្រុកម៉ាឡៃ", "Malai"),
    "0110": ("ក្រុងប៉ោយប៉ែត", "Poipet"),
    # 02 Battambang
    "0201": ("ស្រុកបាណន់", "Banan"),
    "0202": ("ស្រុកថ្មគោល", "Thma Koul"),
    "0203": ("ក្រុងបាត់ដំបង", "Battambang"),
    "0204": ("ស្រុកបវេល", "Bavel"),
    "0205": ("ស្រុកឯកភ្នំ", "Ek Phnum"),
    "0206": ("ស្រុកមោងឫស្សី", "Moung Ruessei"),
    "0207": ("ស្រុករតនមណ្ឌល", "Rotanak Mondol"),
    "0208": ("ស្រុកសង្កែ", "Sangkae"),
    "0209": ("ស្រុកសំឡូត", "Samlout"),
    "0210": ("ស្រុកសំពៅលូន", "Sampov Loun"),
    "0211": ("ស្រុកភ្នំព្រឹក", "Phnum Proek"),
    "0212": ("ស្រុកកំរៀង", "Kamrieng"),
    "0213": ("ស្រុកកោះក្រឡ", "Koas Krala"),
    "0214": ("ស្រុករុក្ខគិរី", "Rukh Kiri"),
    # 03 Kampong Cham
    "0301": ("ស្រុកបាធាយ", "Batheay"),
    "0302": ("ស្រុកចំការលើ", "Chamkar Leu"),
    "0303": ("ស្រុកជើងព្រៃ", "Cheung Prey"),
    "0305": ("ក្រុងកំពង់ចាម", "Kampong Cham"),
    "0306": ("ស្រុកកំពង់សៀម", "Kampong Siem"),
    "0307": ("ស្រុកកងមាស", "Kang Meas"),
    "0308": ("ស្រុកកោះសូទិន", "Koh Sotin"),
    "0313": ("ស្រុកព្រៃឈរ", "Prey Chhor"),
    "0314": ("ស្រុកស្រីសន្ធរ", "Srei Santhor"),
    "0315": ("ស្រុកស្ទឹងត្រង់", "Stueng Trang"),
    # 04 Kampong Chhnang
    "0401": ("ស្រុកបរិបូណ៌", "Baribour"),
    "0402": ("ស្រុកជលគិរី", "Chol Kiri"),
    "0403": ("ក្រុងកំពង់ឆ្នាំង", "Kampong Chhnang"),
    "0404": ("ស្រុកកំពង់លែង", "Kampong Leaeng"),
    "0405": ("ស្រុកកំពង់ត្រឡាច", "Kampong Tralach"),
    "0406": ("ស្រុករលាប្អៀរ", "Rolea B'ier"),
    "0407": ("ស្រុកសាមគ្គីមានជ័យ", "Sameakki Mean Chey"),
    "0408": ("ស្រុកទឹកផុស", "Tuek Phos"),
    # 05 Kampong Speu
    "0501": ("ស្រុកបសេដ្ឋ", "Basedth"),
    "0502": ("ក្រុងច្បារមន", "Chbar Mon"),
    "0503": ("ស្រុកគងពិសី", "Kong Pisei"),
    "0504": ("ស្រុកឱរ៉ាល់", "Aoral"),
    "0506": ("ស្រុកឧដុង្គ", "Odongk"),
    "0507": ("ស្រុកភ្នំស្រួច", "Phnum Sruoch"),
    "0508": ("ស្រុកសំរោងទង", "Samraong Tong"),
    "0509": ("ស្រុកថ្ពង", "Thpong"),
    "0510": ("ស្រុកសាមគ្គីមុនីជ័យ", "Sameakki Muni Chey"),
    # 06 Kampong Thom
    "0601": ("ស្រុកបារាយណ៍", "Baray"),
    "0602": ("ស្រុកកំពង់ស្វាយ", "Kampong Svay"),
    "0603": ("ក្រុងស្ទឹងសែន", "Stueng Saen"),
    "0604": ("ស្រុកប្រាសាទបល្ល័ង្ក", "Prasat Balangk"),
    "0605": ("ស្រុកប្រាសាទសំបូរ", "Prasat Sambour"),
    "0606": ("ស្រុកសណ្តាន់", "Sandan"),
    "0607": ("ស្រុកសន្ទុក", "Santuk"),
    "0608": ("ស្រុកស្ទោង", "Stoung"),
    "0609": ("ស្រុកតាំងគោក", "Taing Kouk"),
    # 07 Kampot
    "0701": ("ស្រុកអង្គរជ័យ", "Angkor Chey"),
    "0702": ("ស្រុកបន្ទាយមាស", "Banteay Meas"),
    "0703": ("ស្រុកឈូក", "Chhouk"),
    "0704": ("ស្រុកជុំគិរី", "Chum Kiri"),
    "0705": ("ស្រុកដងទង់", "Dang Tong"),
    "0706": ("ស្រុកកំពង់ត្រាច", "Kampong Trach"),
    "0707": ("ស្រុកទឹកឈូ", "Tuek Chhou"),
    "0708": ("ក្រុងកំពត", "Kampot"),
    "0709": ("ស្រុកម៉ាកប្រាង្គ", "Makprang"),
    # 08 Kandal
    "0801": ("ស្រុកកណ្តាលស្ទឹង", "Kandal Stueng"),
    "0802": ("ស្រុកគៀនស្វាយ", "Kien Svay"),
    "0803": ("ស្រុកខ្សាច់កណ្តាល", "Khsach Kandal"),
    "0804": ("ស្រុកកោះធំ", "Koh Thom"),
    "0805": ("ស្រុកលើកដែក", "Leuk Daek"),
    "0806": ("ស្រុកអង្គស្នួល", "Angk Snuol"),
    "0807": ("ស្រុកពញាឮ", "Ponhea Lueu"),
    "0808": ("ស្រុកស្អាង", "S'ang"),
    "0809": ("ក្រុងតាខ្មៅ", "Ta Khmau"),
    "0810": ("ស្រុកមុខកំពូល", "Mukh Kampul"),
    "0811": ("ក្រុងអរិយក្សត្រ", "Ariyaksat"),
    "0812": ("ក្រុងសំពៅពូន", "Sampov Poun"),
    "0813": ("ស្រុកស្ទឹងត្រង់ (កណ្តាល)", "Stueng Trang"),
    # 09 Koh Kong
    "0901": ("ស្រុកបូទុមសាគរ", "Botum Sakor"),
    "0902": ("ស្រុកគីរីសាគរ", "Kiri Sakor"),
    "0903": ("ស្រុកកោះកុង", "Koh Kong"),
    "0904": ("ក្រុងខេមរភូមិន្ទ", "Khemara Phoumin"),
    "0905": ("ស្រុកមណ្ឌលសីមា", "Mondol Seima"),
    "0906": ("ស្រុកស្រែអំបិល", "Srae Ambel"),
    "0907": ("ស្រុកថ្មបាំង", "Thma Bang"),
    # 10 Kratie
    "1001": ("ស្រុកឆ្លូង", "Chhloung"),
    "1002": ("ក្រុងក្រចេះ", "Kratie"),
    "1003": ("ស្រុកព្រែកប្រសព្វ", "Prek Prasab"),
    "1004": ("ស្រុកសំបូរ", "Sambour"),
    "1005": ("ស្រុកស្នួល", "Snuol"),
    "1006": ("ស្រុកចិត្របុរី", "Chet Borei"),
    "1007": ("ស្រុកអូរគ្រៀងសែនជ័យ", "Ou Krieng Saen Chey"),
    # 11 Mondulkiri
    "1101": ("ស្រុកកែវសីមា", "Keo Seima"),
    "1102": ("ស្រុកកោះញែក", "Koh Nhek"),
    "1103": ("ស្រុកអូររាំង", "Ou Reang"),
    "1104": ("ស្រុកពេជ្រាដា", "Pech Chreada"),
    "1105": ("ក្រុងសែនមនោរម្យ", "Sen Monorom"),
    # 12 Phnom Penh
    "1201": ("ខណ្ឌចំការមន", "Khan Chamkar Mon"),
    "1202": ("ខណ្ឌដូនពេញ", "Khan Doun Penh"),
    "1203": ("ខណ្ឌ៧មករា", "Khan 7 Makara"),
    "1204": ("ខណ្ឌទួលគោក", "Khan Tuol Kouk"),
    "1205": ("ខណ្ឌដង្កោ", "Khan Dangkao"),
    "1206": ("ខណ្ឌមានជ័យ", "Khan Mean Chey"),
    "1207": ("ខណ្ឌឫស្សីកែវ", "Khan Ruessei Kaev"),
    "1208": ("ខណ្ឌសែនសុខ", "Khan Sen Sok"),
    "1209": ("ខណ្ឌពោធិ៍សែនជ័យ", "Khan Pur Senchey"),
    "1210": ("ខណ្ឌជ្រោយចង្វារ", "Khan Chrouy Changvar"),
    "1211": ("ខណ្ឌព្រែកព្នៅ", "Khan Praek Pnov"),
    "1212": ("ខណ្ឌច្បារអំពៅ", "Khan Chbar Ampov"),
    "1213": ("ខណ្ឌបឹងកេងកង", "Khan Boeng Keng Kang"),
    "1214": ("ខណ្ឌកំបូល", "Khan Kamboul"),
    # 13 Preah Vihear
    "1301": ("ស្រុកជ័យសែន", "Chey Saen"),
    "1302": ("ស្រុកឆែប", "Chhaeb"),
    "1303": ("ស្រុកជាំក្សាន្ត", "Choam Khsant"),
    "1304": ("ស្រុកគូលែន", "Kulen"),
    "1305": ("ស្រុករវៀង", "Rovieng"),
    "1306": ("ស្រុកសង្គមថ្មី", "Sangkum Thmei"),
    "1307": ("ស្រុកត្បែងមានជ័យ", "Tbaeng Mean Chey"),
    "1308": ("ក្រុងព្រះវិហារ", "Preah Vihear"),
    # 14 Prey Veng
    "1401": ("ស្រុកបាភ្នំ", "Ba Phnum"),
    "1402": ("ស្រុកកំចាយមារ", "Kamchay Mear"),
    "1403": ("ស្រុកកំពង់ត្របែក", "Kampong Trabaek"),
    "1404": ("ស្រុកកញ្ច្រៀច", "Kanhchriech"),
    "1405": ("ស្រុកមេសាង", "Me Sang"),
    "1406": ("ស្រុកពាមជរ", "Peam Chor"),
    "1407": ("ស្រុកពាមរ", "Peam Ro"),
    "1408": ("ស្រុកពារាំង", "Pea Reang"),
    "1409": ("ស្រុកព្រះស្តេច", "Preah Sdach"),
    "1410": ("ក្រុងព្រៃវែង", "Prey Veng"),
    "1411": ("ស្រុកពោធិ៍រៀង", "Pur Rieng"),
    "1412": ("ស្រុកស៊ីធរកណ្តាល", "Sithor Kandal"),
    "1413": ("ស្រុកស្វាយអន្ធរ", "Svay Antor"),
    # 15 Pursat
    "1501": ("ស្រុកបាកាន", "Bakan"),
    "1502": ("ស្រុកកណ្តៀង", "Kandieng"),
    "1503": ("ស្រុកក្រគរ", "Krakor"),
    "1504": ("ស្រុកភ្នំក្រវាញ", "Phnum Kravanh"),
    "1505": ("ក្រុងពោធិ៍សាត់", "Pursat"),
    "1506": ("ស្រុកវាលវែង", "Veal Veang"),
    "1507": ("ស្រុកតាលោសែនជ័យ", "Talo Senchey"),
    # 16 Ratanakiri
    "1601": ("ស្រុកអណ្តូងមាស", "Andoung Meas"),
    "1602": ("ក្រុងបានលុង", "Ban Lung"),
    "1603": ("ស្រុកបរកែវ", "Bar Kaev"),
    "1604": ("ស្រុកកូនមុំ", "Koun Mom"),
    "1605": ("ស្រុកលំផាត់", "Lumphat"),
    "1606": ("ស្រុកអូរជុំ", "Ou Chum"),
    "1607": ("ស្រុកអូរយ៉ាដាវ", "Ou Ya Dav"),
    "1608": ("ស្រុកតាវែង", "Ta Veaeng"),
    "1609": ("ស្រុកវើនសៃ", "Veun Sai"),
    # 17 Siem Reap
    "1701": ("ស្រុកអង្គរជុំ", "Angkor Chum"),
    "1702": ("ស្រុកអង្គរធំ", "Angkor Thom"),
    "1703": ("ស្រុកបន្ទាយស្រី", "Banteay Srei"),
    "1704": ("ស្រុកជីក្រែង", "Chi Kraeng"),
    "1706": ("ស្រុកក្រឡាញ់", "Kralanh"),
    "1707": ("ស្រុកពួក", "Puok"),
    "1709": ("ស្រុកប្រាសាទបាគង", "Prasat Bakong"),
    "1710": ("ក្រុងសៀមរាប", "Siem Reap"),
    "1711": ("ស្រុកសូទ្រនិគម", "Soutr Nikom"),
    "1712": ("ស្រុកស្រីស្នំ", "Srei Snam"),
    "1713": ("ស្រុកស្វាយលើ", "Svay Leu"),
    "1714": ("ស្រុកវ៉ារិន", "Varin"),
    "1715": ("ក្រុងរុនតាឯកតេជោសែន", "Run Ta Ek Techo Sen"),
    # 18 Preah Sihanouk
    "1801": ("ក្រុងព្រះសីហនុ", "Preah Sihanouk"),
    "1802": ("ស្រុកព្រៃនប់", "Prey Nob"),
    "1803": ("ស្រុកស្ទឹងហាវ", "Stueng Hav"),
    "1804": ("ស្រុកកំពង់សិលា", "Kampong Seila"),
    "1805": ("ក្រុងកោះរ៉ុង", "Koh Rong"),
    "1806": ("ក្រុងកំពង់សោម", "Kampong Saom"),
    # 19 Stung Treng
    "1901": ("ស្រុកសេសាន", "Sesan"),
    "1902": ("ស្រុកសៀមបូក", "Siem Bouk"),
    "1903": ("ស្រុកសៀមប៉ាង", "Siem Pang"),
    "1904": ("ក្រុងស្ទឹងត្រែង", "Stung Treng"),
    "1905": ("ស្រុកថាឡាបរិវ៉ាត់", "Thala Barivat"),
    "1906": ("ស្រុកបូរីអូរស្វាយសែនជ័យ", "Borei Ou Svay Sen Chey"),
    # 20 Svay Rieng
    "2001": ("ស្រុកចន្ទ្រា", "Chantrea"),
    "2002": ("ស្រុកកំពង់រោទិ៍", "Kampong Rou"),
    "2003": ("ស្រុករំដួល", "Romdoul"),
    "2004": ("ស្រុករមាសហែក", "Romeas Haek"),
    "2005": ("ស្រុកស្វាយជ្រុំ", "Svay Chrum"),
    "2006": ("ក្រុងស្វាយរៀង", "Svay Rieng"),
    "2007": ("ស្រុកស្វាយទាប", "Svay Teab"),
    "2008": ("ក្រុងបាវិត", "Bavet"),
    # 21 Takeo
    "2101": ("ស្រុកអង្គរបុរី", "Angkor Borei"),
    "2102": ("ស្រុកបាទី", "Bati"),
    "2103": ("ស្រុកបូរីជលសារ", "Borei Cholsar"),
    "2104": ("ស្រុកគិរីវង់", "Kiri Vong"),
    "2105": ("ស្រុកកោះអណ្តែត", "Koh Andaet"),
    "2106": ("ស្រុកព្រៃកប្បាស", "Prey Kabbas"),
    "2107": ("ស្រុកសំរោង (តាកែវ)", "Samraong"),
    "2108": ("ក្រុងដូនកែវ", "Doun Kaev"),
    "2109": ("ស្រុកត្រាំកក់", "Tram Kak"),
    "2110": ("ស្រុកទ្រាំង", "Treang"),
    # 22 Oddar Meanchey
    "2201": ("ស្រុកអន្លង់វែង", "Anlong Veng"),
    "2202": ("ស្រុកបន្ទាយអំពិល", "Banteay Ampil"),
    "2203": ("ស្រុកចុងកាល់", "Chong Kal"),
    "2204": ("ក្រុងសំរោង", "Samraong"),
    "2205": ("ស្រុកត្រពាំងប្រាសាទ", "Trapeang Prasat"),
    # 23 Kep
    "2301": ("ស្រុកដំណាក់ចង្អើរ", "Damnak Chang'aeur"),
    "2302": ("ក្រុងកែប", "Kep"),
    # 24 Pailin
    "2401": ("ក្រុងប៉ៃលិន", "Pailin"),
    "2402": ("ស្រុកសាលាក្រៅ", "Sala Krau"),
    # 25 Tboung Khmum
    "2501": ("ស្រុកអូររាំងឪ", "Ou Reang Ov"),
    "2502": ("ស្រុកក្រូចឆ្មារ", "Krouch Chhmar"),
    "2503": ("ស្រុកមេមត់", "Memot"),
    "2504": ("ស្រុកពញាក្រែក", "Ponhea Kraek"),
    "2505": ("ស្រុកត្បូងឃ្មុំ", "Tboung Khmum"),
    "2506": ("ក្រុងសួង", "Suong"),
    "2507": ("ស្រុកតំបែរ", "Dambae")
}

def import_cambodia_locations(csv_path="doc/CambodiaCommuneList2025.csv"):
    if not os.path.exists(csv_path):
        return {'success': False, 'error': f"File not found: {csv_path}"}

    # 1. Insert/Update Provinces
    for p_code, (p_kh, p_en) in PROVINCES_DATA.items():
        prov = db.session.get(Province, p_code)
        if not prov:
            prov = Province(code=p_code, name_kh=p_kh, name_en=p_en)
            db.session.add(prov)
        else:
            prov.name_kh = p_kh
            prov.name_en = p_en
    db.session.commit()

    # 2. Insert/Update Districts
    for d_code, (d_kh, d_en) in DISTRICTS_DATA.items():
        p_code = d_code[:2]
        dist = db.session.get(District, d_code)
        if not dist:
            dist = District(code=d_code, province_code=p_code, name_kh=d_kh, name_en=d_en)
            db.session.add(dist)
        else:
            dist.name_kh = d_kh
            dist.name_en = d_en
    db.session.commit()

    # 3. Read Communes from CSV
    commune_count = 0
    with open(csv_path, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            p_code = row.get('province_code', '').strip().zfill(2)
            d_code = row.get('district_code', '').strip().zfill(4)
            c_code = row.get('commune_code', '').strip().zfill(6)
            c_kh = row.get('commune_kh', '').strip()
            c_en = row.get('commune_en', '').strip()

            dist = db.session.get(District, d_code)
            if not dist:
                dist = District(
                    code=d_code,
                    province_code=p_code,
                    name_kh=f"ស្រុក/ខណ្ឌ {d_code}",
                    name_en=f"District {d_code}"
                )
                db.session.add(dist)
                db.session.flush()

            comm = db.session.get(Commune, c_code)
            if not comm:
                comm = Commune(
                    code=c_code,
                    district_code=d_code,
                    province_code=p_code,
                    name_kh=c_kh,
                    name_en=c_en
                )
                db.session.add(comm)
            else:
                comm.name_kh = c_kh
                comm.name_en = c_en
                comm.district_code = d_code
                comm.province_code = p_code

            commune_count += 1
            if commune_count % 300 == 0:
                db.session.commit()

    db.session.commit()
    return {
        'success': True,
        'provinces': len(PROVINCES_DATA),
        'districts': len(DISTRICTS_DATA),
        'communes': commune_count
    }

if __name__ == "__main__":
    from flask import Flask
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///hrms.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(app)
    with app.app_context():
        db.create_all()
        import_cambodia_locations()
