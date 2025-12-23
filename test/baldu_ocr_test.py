import requests


def main():
    url = "https://aip.baidubce.com/oauth/2.0/token?grant_type=client_credentials&client_id=I7pQrwb08r1JLTAhIJ8VnHV2&client_secret=iWC7yz12tQgKh2aEZLBIlabxZPlHV56X"

    payload = ""
    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json'
    }

    response = requests.request("POST", url, headers=headers, data=payload)
    for k,v in response.json().items():
        print(k,v)


if __name__ == '__main__':
    main()