from bs4 import BeautifulSoup
import requests
import re


def get_case_info(case_number, county, hdr=None):
    # case_number - general format case number for oscn.net (e.g. CF-2022-123)
    # county      - name of county of case (e.g. "oklahoma" or "tulsa")
    # hdr         - request headers, blank defaults to minimum requirement for oscn.net : optional

    if hdr is None:
        hdr = {'User-Agent': 'Mozilla/5.0'}  # request header needed for response

    url = f"https://www.oscn.net/dockets/GetCaseInformation.aspx?db={county}&number={case_number}"
    page = requests.get(url, headers=hdr).content
    soup = BeautifulSoup(page, 'html.parser')
    soup_text = soup.text

    # raise error if captcha
    if "CAPTCHA" in soup.text.upper():
        raise ConnectionError("OSCN Captcha Detected", url)

    # case_info dictionary to be returned
    case_info = {
        'case_number': case_number,
        'case_type': '',
        'judgment': '',
        'plaintiff': '',
        'defendant': '',
        'filed_date': '',
        'closed_date': '',
        'judge': '',
        'oscn_link': url
    }

    # finds case type by regex
    regex_result = re.search(r"No\..*\((.*)\).*Filed:\s\d", soup_text, flags=re.DOTALL)
    try:
        case_type = regex_result.group(1)
    except AttributeError:
        case_type = "Not Found"
    case_info['case_type'] = case_type

    # finds judgments by font color and regex
    # handles multiple dispositions on single case
    if "Disposed:" in soup_text:
        dispositions = soup.find_all('font', {'color': 'red'})
        if len(dispositions) > 1:  # if there are multiple dispositions
            results = []  # results of each disposition
            for disposition in dispositions:
                regex_result = re.search(r"Disposed:(.*),", disposition.text, flags=re.DOTALL)
                try:
                    result = regex_result.group(1).strip()
                except AttributeError:
                    result = "Error Reading Disposition"
                results.append(result)
            judgment = " && ".join(results)  # multiple dispositions joined by '&&'
        else:  # if there is a single disposition
            disposition_search_text = dispositions[0].text
            regex_result = re.search(r"Disposed:(.*),", disposition_search_text, flags=re.DOTALL)
            try:
                judgment = regex_result.group(1).strip()
            except AttributeError:
                judgment = "Not Found"
    else:  # if no disposition found on page
        judgment = "Disposition Pending"
    case_info['judgment'] = judgment

    # variables for later
    case_style_soup = soup.find('table', {'class': 'caseStyle'})
    case_style_soup_text = case_style_soup.text
    case_style_soup_td_text = case_style_soup.td.text
    case_style_td_text_list = case_style_soup_td_text.upper().split("V.")

    # finds plaintiffs, handles multiple plaintiffs
    plaintiffs_raw = case_style_td_text_list[0]  # plaintiffs text from case style
    plaintiffs_raw = " ".join(plaintiffs_raw.split())  # removes duplicate white spaces
    plaintiffs_list_raw = plaintiffs_raw.split(", PLAINTIFF")  # splits into list based on each plaintiff
    plaintiff_list = []
    for plaintiff in plaintiffs_list_raw:
        plaintiff = plaintiff.replace(", AND ", "")
        plaintiff = plaintiff.replace(",", "").replace(".", "")
        plaintiff = plaintiff.strip()
        if plaintiff:  # if list index isn't blank
            plaintiff_list.append(plaintiff)
    plaintiff = " && ".join(plaintiff_list)
    case_info['plaintiff'] = plaintiff

    # finds defendants, handles multiple defendants
    defendants_raw = case_style_td_text_list[1]  # defendants text from case style
    defendants_raw = " ".join(defendants_raw.split())  # removes duplicate white spaces
    defendants_list_raw = defendants_raw.split(", DEFENDANT")  # splits into list based on each defendant
    defendant_list = []
    for defendant in defendants_list_raw:
        defendant = defendant.replace(".", "")
        defendant = defendant.replace(", AND ", "")
        defendant = defendant.strip()
        if defendant:  # if list index isn't blank
            defendant_list.append(defendant)
    defendant = " && ".join(defendant_list)
    case_info['defendant'] = defendant

    # finds case filed date by regex
    regex_result = re.search(r"Filed:\s(\d\d/\d\d/\d\d\d\d)", soup_text, flags=re.DOTALL)
    try:
        filed_date = regex_result.group(1)
    except AttributeError:
        filed_date = "Not found"
    case_info['filed_date'] = filed_date

    # finds case closed date by regex
    regex_result = re.search(r"Closed:\s(\d\d/\d\d/\d\d\d\d)", soup_text, flags=re.DOTALL)
    try:
        closed_date = regex_result.group(1)
    except AttributeError:
        closed_date = "Not found"
    case_info['closed_date'] = closed_date

    # finds judge of case by regex
    regex_result = re.search(r"Filed:.*Judge:(.*)", case_style_soup_text, flags=re.DOTALL)
    try:
        judge = regex_result.group(1).replace("\n", "").strip()
    except AttributeError:
        judge = "Not found"
    case_info['judge'] = judge

    return case_info


# example use case
if __name__ == "__main__":

    # create list of case numbers
    case_abbr = input("2 Letter Case Abbreviation: ")
    case_year = input("Full Case Year (20XX): ")
    start_case_number = int(input("Starting Number: "))
    end_case_number = int(input("Ending Number: "))

    list_of_case_numbers = []
    for i in range(end_case_number - start_case_number + 1):
        num = i + start_case_number
        case_number_to_add = f"{case_abbr}-{case_year}-{num}"
        list_of_case_numbers.append(case_number_to_add)

    # loop through multiple case numbers and add to list of dicts
    # way of dealing with captcha by opening webbrowser
    import webbrowser
    case_info_list = []  # list of dicts
    for case_num in list_of_case_numbers:
        while True:
            try:
                case = get_case_info(case_num, county='tulsa')
                print(case)
                break
            except ConnectionError as e:
                print(e)
                webbrowser.open(e.args[1])
                input("Captcha Detected, please solve and press Enter to continue...")
        case_info_list.append(case)

    # write to csv file
    import csv
    with open("output.csv", "w", newline="") as f:

        fieldnames = [
            'case_number',
            'case_type',
            'judgment',
            'plaintiff',
            'defendant',
            'filed_date',
            'closed_date',
            'judge',
            'oscn_link',
        ]

        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for case in case_info_list:
            writer.writerow(case)
