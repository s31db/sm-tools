from datetime import date, timedelta
from jours_feries_france import JoursFeries
import xlsxwriter


def prepare_calendar():
    workbook = xlsxwriter.Workbook("demo.xlsx")
    worksheet = workbook.add_worksheet()
    default = workbook.add_format({"center_across": True})
    sep = workbook.add_format({"center_across": True, 'left': 1})

    start = date.fromisoformat('2023-01-01')
    p = None
    n = 2
    for i in range(1, 366):
        d = start + timedelta(days=i)
        if d.weekday() < 5 and not JoursFeries.is_bank_holiday(d):
            print(d.strftime('%d/%m/%Y'), end='\t')
            if p and p.weekday() > d.weekday():
                format_cell = sep
                for c in range(2, 11):
                    worksheet.write(c, n, '', format_cell)
            else:
                format_cell = default
            worksheet.write(0, n, d.strftime('%A'), format_cell)
            worksheet.write(1, n, d.strftime('%d/%m/%Y'), format_cell)
            p = d
            n += 1


if __name__ == '__main__':
    prepare_calendar()
