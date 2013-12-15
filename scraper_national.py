from selenium import webdriver
from bs4 import BeautifulSoup
import csv
import dataset


def contrib_link(i):
    try:
        value = ((row.find("td", headers=i).a).string).encode("utf-8", "ignore")
    except:
        value = "N/A"
        pass
    return value


def contrib_text(i):
    try:
        value = (row.find("td", headers=i).string).encode("utf-8", "ignore")
    except:
        value = "N/A"
        pass
    return value


def contrib_number(i):
    try:
        value = ((row.find("td", headers=i).span).string).encode("utf-8", "ignore")
    except:
        value = "N/A"
        pass
    return value


def get_donor_info(donor_soup, i):
    try:
        value = (donor_soup.find("input", id=i)['value']).encode("utf-8", "ignore")
    except:
        value = "N/A"
        pass
    return value


def donor_info(i):
    driver.get(i)
    donor_html = driver.page_source
    donor_soup = BeautifulSoup(donor_html)
    donor_name = get_donor_info(donor_soup, "aifullname")
    donor_city = get_donor_info(donor_soup, "city")
    donor_province = get_donor_info(donor_soup, "province")
    donor_postalcode = get_donor_info(donor_soup, "postalcode")
    value = (donor_name, donor_city, donor_province, donor_postalcode)
    return value

def next_page(i):
    try:
        driver.find_element_by_xpath("//a[@id='nextpagelink']").click()
        value = i + 1
    except:
        value = 0
    return value
    
def get_html(page):
    start_url = "http://www.elections.ca/WPAPPS/WPF/Home/PP/SelectParties?act=C2&returntype=1&period=0"
    driver.get(start_url)
    driver.find_element_by_xpath("//select[@id='fromperiod']/option[text()='2012']").click()
    driver.find_element_by_xpath("//input[@id='buttonAddParties']").click()
    driver.find_element_by_xpath("//input[@id='buttonSelectAll']").click()
    driver.find_element_by_xpath("//input[@id='buttonSearchSelected']").click()
    driver.find_element_by_xpath("//a[@id='SelectContributions4lnk']").click()
    driver.find_element_by_xpath("//input[@id='buttonFind']").click()
    queryid = (driver.current_url.split('&'))[8]
    base_url = "http://www.elections.ca/WPAPPS/WPF/Home/PP/ContributionReport?act=C2&returntype=1&option=4&period=0&fromperiod=0&toperiod=0&contribrange=-1&selectallcontribclasses=True&contribclass=1%2C%206%2C%2012&totalReportPages=1008&"
    url = base_url+str(queryid)+"&reportPage="+str(page)
    driver.get(url)
    
db = dataset.connect('sqlite:///ftm_national.db')
datatable = db['2012']
errortable = db['errors']

driver = webdriver.PhantomJS()
#contrib_file = open("2012_annual.csv", "wb")
#error_file = open("errors_2012_annual.csv", "wb")
#writer = csv.writer(contrib_file)
#error_writer = csv.writer(error_file)
#writer.writerow(["name", "city", "province", "postalcode", "party","date","contrib_class","leadership_candidate","monetary","non_monetary","report_type","report_year", "page", "row"])


page = 1
get_html(page)

while page > 0:
    try:
        html = driver.page_source
        soup = BeautifulSoup(html)
        table = soup.find("table", id="ContributionReportData")
        row_count = 0
        
        for row in table.find_all("tr")[1:]:
            try:
                row_count = row_count+1
                name = contrib_link("contr_full_name")
                recipient = contrib_text("entity_name")
                party = (recipient.split(' / ')[0]).strip()
                report_type = recipient.split(' / ')[1]
                report_year = (recipient.split(' / ')[2]).strip()
                date = contrib_number("recvd_dt")
                contrib_class = (contrib_text("contr_class_desc")).strip()
                lead_cand = (contrib_text("lead_cand")).strip()
                monetary = contrib_number("mon_amt")
                non_monetary = contrib_number("non_mon_amt")
                donor_url = row.find("td", headers="contr_full_name").a['href']
                donor_url = "http://www.elections.ca"+donor_url
                contributor = donor_info(donor_url)
                donor_id = "p"+str(page)+"r"+str(row_count)
                contribution = (donor_id,contributor[0],contributor[1],contributor[2],contributor[3],party,date,contrib_class,lead_cand,monetary,non_monetary,report_type,report_year)
                datatable.insert(dict(donor_id=donor_id, name=contributor[0], city=contributor[1], province=contributor[2], postalcode=contributor[3], party=party, date=date, contrib_class=contrib_class, leadership_candidate=lead_cand, monetary=monetary, non_monetary=non_monetary,report_type=report_type,report_year=report_year))
                #writer.writerow(contribution)
                print ','.join(contribution)
        
            except Exception, e:
                print "error encountered at "+donor_id
                #print str(e)
                #contribution = (donor_id, str(e))
                #error_writer.writerow(contribution)
                errortable.insert(dict(donor_id=donor_id, error=str(e)))
                pass
                                 
        page = next_page(page)
    
    except Exception, e:
        print str(e)
        error_writer.writerow("Encountered error on page "+str(page))
        get_html(page)
        pass

#contrib_file.close()