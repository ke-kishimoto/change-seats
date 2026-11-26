"""研修生情報のJSONへの変換と検証。"""

import json

COLUMNS = ["名前", "所属", "性別", "成績", "コミュニケーションスキル"]
GENDERS = ["未入力", "男性", "女性", "その他", "回答しない"]
GRADES = {"A": 5, "B": 4, "C": 3, "D": 2, "E": 1}
COMMUNICATION = {"積極的": 1, "どちらでもない": 0, "消極的": -1}
RATINGS = {"成績": GRADES, "コミュニケーションスキル": COMMUNICATION}


def export_trainees(records, companies=None):
    """空欄を含む入力内容をUTF-8のJSONにする。"""
    encoded = []
    for record in records:
        person = dict(record)
        for key, values in RATINGS.items():
            person[key] = values[person[key]] if person[key] else None
        encoded.append(person)
    return json.dumps({"version": 3, "companies": companies or [], "trainees": encoded}, ensure_ascii=False, indent=2, allow_nan=False).encode("utf-8")


def import_trainees(data):
    """JSONを検証し、画面に表示できる研修生のリストを返す。"""
    try:
        document = json.loads(data.decode("utf-8-sig"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError("保存データの形式が正しくありません。") from exc

    if not isinstance(document, dict) or type(document.get("version")) is not int or document["version"] not in (1, 2, 3) or not isinstance(document.get("trainees"), list):
        raise ValueError("研修生情報の保存形式が正しくありません。")

    companies = document.get("companies", [])
    if not isinstance(companies, list) or any(not isinstance(company, str) or not company.strip() for company in companies) or len(companies) != len(set(companies)):
        raise ValueError("企業情報の保存形式が正しくありません。")
    companies = list(companies)

    result = []
    for index, record in enumerate(document["trainees"], start=1):
        if not isinstance(record, dict) or set(record) != set(COLUMNS):
            raise ValueError(f"{index}行目の項目が正しくありません。")
        if any(not isinstance(record[key], str) for key in ("名前", "所属", "性別")):
            raise ValueError(f"{index}行目の名前・所属・性別は文字列で入力してください。")
        if record["性別"] not in GENDERS and record["性別"] != "":
            raise ValueError(f"{index}行目の性別が選択肢にありません。")
        person = {key: record[key] for key in COLUMNS}
        for key, values in RATINGS.items():
            value = record[key]
            if document["version"] == 1 and value is not None:
                raise ValueError("旧形式の成績・コミュニケーションスキルは新しい評価に自動変換できません。")
            if value is not None and (type(value) is not int or value not in values.values()):
                raise ValueError(f"{index}行目の{key}の値が正しくありません。")
            person[key] = next((label for label, number in values.items() if number == value), None)
        result.append(person)
        company = person["所属"]
        if document["version"] < 3 and company and company not in companies:
            companies.append(company)
    return result, companies
