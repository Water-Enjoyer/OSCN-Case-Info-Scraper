# OSCN-Case-Info-Scraper
Python function for scraping basic case information from the Oklahoma State Courts Network website (oscn.net).

Function takes 3 inputs, 2 required.
```
def get_case_info(case_number, county, hdr=None):
    # case_number - general format case number for oscn.net (e.g. CF-2022-123)
    # county      - name of county of case (e.g. "oklahoma" or "tulsa")
    # hdr         - request headers, blank defaults to minimum requirement for oscn.net : optional
```

Returns dictionary of the following.
```
    case_info = {
        'case_number':
        'case_type':
        'judgment':
        'plaintiff':
        'defendant':
        'filed_date':
        'closed_date':
        'judge':
        'oscn_link':
    }
```

Handles multiple dispositions (judgments), plaintiffs, and defendants. Prints them seperated by `&&`.
```
>>> case_info['judgment']
>>> DEFAULT JUDGEMENT && DISMISSED - RELEASE AND SATISFIED
>>> case_info['plaintiff']
>>> JOHN DOE && JANE DOE
```

Captcha raises ConnectionError with URL of captcha as `.args[1]`.
This allows you to catch captchas and deal with them in any way you choose.
A simple example is included using webbrowser to manually solve the captcha.
```
import webbrowser
    case_info_list = []  # list of dicts
    for case_num in list_of_case_numbers:
        while True:
            try:
                case = get_case_info(case_num, county='tulsa')
                break
            except ConnectionError as e:
                webbrowser.open(e.args[1])
                input("Captcha Detected, please solve and press Enter to continue...")
        case_info_list.append(case)
```
