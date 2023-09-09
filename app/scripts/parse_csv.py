import csv
import uuid
from datetime import datetime

with open('static/games.csv', newline='') as csvfile:
    reader = csv.DictReader(csvfile, delimiter=',')
    with open('db/03_parsed_data.sql', mode="wt") as f:
        for x, row in enumerate(reader):
            if x == 0:
                continue

            for key, val in row.items():
                row[key] = val.replace('"', '\\"')

            row["id"] = str(uuid.uuid4())

            rls_date = row["Release Date"]
            if rls_date == "Early Access":
                row["processed_rls_date"] = "NULL"    
                row["early_access"] = "TRUE"
            else:
                datestr = datetime.strptime(rls_date, '%m/%d/%Y').strftime('%Y-%m-%d')
                row["processed_rls_date"] = f'"{datestr}"'
                row["early_access"] = "DEFAULT"

            row["rls_region"] = row["Release Region"]

            row["VR"] = "TRUE" if row["VR"] == 1 else "FALSE"
            row["DLC"] = "TRUE" if row["DLC"] == 1 else "FALSE"

            row["English"] = int(row["English"]) if row["English"] != "" else 0

            row["Owned"] = "TRUE" if row["Owned"] == 1 else "FALSE"

            prch_date = row["Date Purchased"] 
            if prch_date == "":
                row["processed_purchase_date"] = "NULL"
            else:
                datestr = datetime.strptime(prch_date, '%m/%d/%Y').strftime('%Y-%m-%d')
                row["processed_purchase_date"] = f'"{datestr}"'

            prch_price = row[" Purchase Price "]
            if prch_price == "" or prch_price == " $ -   ":
                row["processed_purchase_price"] = "NULL"
            else:
                row["processed_purchase_price"] = float(prch_price.replace('$', ''))

            row["processed_format"] = row["Format"].lower()
            if row["processed_format"] == "":
                row["processed_format"] = "NULL"
            else:
                row["processed_format"] = '"%s"' % (row["processed_format"])

            row["Completed"] = "TRUE" if row["Completed"] == 1 else "FALSE"

            cmplt_date = row["Date Completed"]
            if cmplt_date == "":
                row["processed_cmplt_date"] = "NULL"
            else:
                try:
                    datestr = datetime.strptime(cmplt_date, '%m/%d/%Y').strftime('%Y-%m-%d')
                    row["processed_cmplt_date"] = f'"{datestr}"'
                except ValueError:
                    datestr = datetime.strptime(cmplt_date, '%m/%Y').strftime('%Y-%m')
                    row["processed_cmplt_date"] = f'"{datestr}"'

            cmplt_time = row["Completion Time"]
            if cmplt_time == "":
                row["cmplt_time"] = "NULL"
            else:
                row["cmplt_time"] = float(cmplt_time)
            
            if row["Rating"]:
                row["Rating"] = float(row["Rating"].replace("%", "")) / 100
            else:
                row["Rating"] = "NULL"
            row["metacritic_rating"] = float(row["Metacritic Rating"].replace("%", "") if row["Metacritic Rating"] else 0) / 100
            row["gamefaqs_rating"] = float(row["GameFAQs User Rating"].replace("%", "") if row["GameFAQs User Rating"] else 0) / 100

            row["Priority"] = float(row["Priority"]) if row["Priority"] else "NULL"
            row["Wishlisted"] = "TRUE" if row["Wishlisted"] == 1 else "FALSE"

            row["est_time"] = float(row["Estimated Time"]) if not row["Estimated Time"] == " " and not row["Estimated Time"] == "" else "NULL"

            row["processed_play_status"] = int(row["Playing Status"]) if row["Playing Status"] else 0


            rls_year = row["Release Year"]
            if rls_year == "Early Access" or rls_year == "":    
                row["processed_rls_year"] = 0
            else:
                row["processed_rls_year"] = int(rls_year)

            f.write('INSERT INTO games VALUES (%s);\n' % (
                '"{id}", "{Title}", "{Platform}", {processed_rls_date}, {early_access}, "{rls_region}", "{Publisher}", "{Developer}", "{Franchise}", "{Genre}", {VR}, {DLC}, {English}, {Owned}, "{Condition}", {processed_purchase_date}, {processed_purchase_price}, {processed_format}, {Completed}, {processed_cmplt_date}, {cmplt_time}, {Rating}, {metacritic_rating}, {gamefaqs_rating}, "{Notes}", {Priority}, {Wishlisted}, {est_time}, {processed_play_status}, {processed_rls_year}'.format_map(row)))
