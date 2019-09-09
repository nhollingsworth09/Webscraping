# -*- coding: utf-8 -*-
'''
Same improvements as AZLyrics spider
'''

import requests
from bs4 import BeautifulSoup
import pandas as pd
import numpy as np
import time, datetime
import traceback
import re
import os

class Edmunds_Spider():
    def __init__(self):
        self.max_pro = 4
        self.max_con = 4
        self.url = "https://www.edmunds.com/"
        self.header = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/76.0.3809.132 Safari/537.36"}
        self.car_year = []
        self.car_model = []
        self.car_model_num = []
        self.edmunds_overall = []
        self.edmunds_driving = []
        self.edmunds_comfort = []
        self.edmunds_interior = []
        self.edmunds_utility = []
        self.edmunds_technology = []
        self.consumer_rating = []
        self.consumer_total = []
        self.consumer_rating_5 = []
        self.consumer_rating_4 = []
        self.consumer_rating_3 = []
        self.consumer_rating_2 = []
        self.consumer_rating_1 = []
        self.pros1 = []
        self.pros2 = []
        self.pros3 = []
        self.pros4 = []
        self.cons1 = []
        self.cons2 = []
        self.cons3 = []
        self.cons4 = []
    
    def get_scrape_dict(self, filename):        
        self.scrape_dict = pd.read_excel(filename, sheet_name="scrape_dict")
        
        self.makes = self.scrape_dict.loc[:,'make']
        self.models = self.scrape_dict.loc[:, 'model']
        self.bodies = self.scrape_dict.loc[:, 'body']
        self.model_nums = self.scrape_dict.loc[:, 'model_number_new']
        
        self.years = {'2017', '2018', '2019'}
            
    def response_tests(self):
        STATUS = []
        CARS = []
        
        start = time.time()
        for make, model, body in zip(self.makes, self.models, self.bodies):
            for year in self.years:
                #- Need to change the layout of this depending on the car
                if body == 'None':
                    car = make+'/'+model+'/'+year+'/review/'
                elif make == 'MINI':
                    #Edmunds does not use 'Cooper' in it's Mini URLS
                    car = make+'/'+body+'/'+year+'/review/'
                elif make == 'Mercedes-Benz' and body == 'Maybach':
                    car = make+'/'+body+'/'+year+'/review/'
                else:
                    car = make+'/'+model+'/'+year+'/'+body+'/review/'
                
                car = car.lower()
                page = requests.get(self.url+car, headers=self.header)
                
                CARS.append(car)
                STATUS.append(page.status_code)
                print('.')

        end = time.time()
        runtime = end - start

        print('Runtime: {}'.format(str(datetime.timedelta(seconds = round(runtime)))))

        responses = pd.DataFrame({'address':CARS, 'status':STATUS})
        responses.to_excel('HTTP_Testing.xlsx', sheet_name='Responses', index=False)

        return "HTTP Responses saved as 'HTTP_Testing.xlsx'"

    def get_scorecard(self, page_soup):
        KEYS = ['overall', 'driving', 'comfort', 'interior', 'utility','technology']
        try:
            scorecard = page_soup.find('div', class_='scorecard').select("tr")
            scorecard_dict = dict(map(lambda rating: (list(rating.children)[0].get_text().lower(), float(list(rating.children)[1].get_text()[:3])), scorecard))
            
            for key in KEYS:
                if key not in scorecard_dict.keys():
                    scorecard_dict[key] = 'None'
            
            return scorecard_dict
          
        except AttributeError:
            return {'overall': 'None', 'driving': 'None', 'comfort': 'None', 'interior': 'None', 'utility': 'None', 'technology': 'None'}
        
    def get_consumer_ratings(self, page_soup):
        no_reviews = page_soup.select('section.consumer-reviews div')[1].get_text()
        
        if re.match('Be the first to write a review', no_reviews, re.IGNORECASE):
            consumer_ratings = dict({'5': 'None', '4': 'None', '3': 'None', '2': 'None', '1': 'None'})
            total_reviews = 0
            consumer_total = 'None'
            
        else:
            try:
                consumer_ratings = dict(map(lambda rating: (rating.get_text().split(': ')[0][0], round(int(rating.get_text().split(': ')[1][:-1])/100, 2)), page_soup.select('section.consumer-reviews div')[:5]))
                total_reviews = int(page_soup.select('section.consumer-reviews div')[5].get_text().split(' ')[7])
                consumer_total = float(page_soup.select('section.consumer-reviews div')[5].get_text().split(' ')[3])
            except IndexError:
                consumer_ratings = dict(map(lambda rating: (rating.get_text()[0], round(int(rating.get_text()[2:-2])/100,2)), page_soup.select('section.consumer-reviews div.summary-rating')))
                total_reviews = int(page_soup.select('section.consumer-reviews div.review-count')[0].get_text()[:-8])
                consumer_total = float(page_soup.select('section.consumer-reviews span.average-user-rating')[0].get_text())
        
        return consumer_total, total_reviews, consumer_ratings
    
    def get_pro_con(self, page_soup):
        current_pros = []
        current_cons = []
    
        for __ in page_soup.select('li.pro-con-li span'):
    
    
          pro_con_list = list(__.children)
          text = pro_con_list[1]
    
          class_condition = pro_con_list[0].has_attr('class')
          pro_condition = 'icon-checkmark' in pro_con_list[0]['class']
          con_condition = 'icon-cross3' in pro_con_list[0]['class']
    
          if len(current_pros) == self.max_pro and pro_condition:
            continue
          elif len(current_cons) == self.max_con and con_condition:
            continue
          elif class_condition and pro_condition:   
            current_pros.append(text)
          elif class_condition and con_condition:
            current_cons.append(text)
        
        if len(current_pros) < self.max_pro:
            current_pros.extend(list(np.repeat(['None'], self.max_pro-len(current_pros), axis=0)))
    
        if len(current_cons) < self.max_con:
          current_cons.extend(list(np.repeat(['None'], self.max_con-len(current_cons), axis=0)))
        
        return current_pros, current_cons   

    def execute_scrape(self):
        for make, model, body, model_num in zip(self.makes, self.models, self.bodies, self.model_nums):
            for year in self.years:
                #- Need to change the layout of URL depending on the car
                if body == 'None':
                    car = make+'/'+model+'/'+year+'/review/'
                elif make == 'MINI':
                    #- Edmunds does not use 'Cooper' in it's Mini URLS
                    car = make+'/'+body+'/'+year+'/review/'
                elif make == 'Mercedes-Benz' and body == 'Maybach':
                    car = make+'/'+body+'/'+year+'/review/'
                else:
                    car = make+'/'+model+'/'+year+'/'+body+'/review/'
        
                try:
                    car = car.lower()
                    page = requests.get(self.url+car, headers=self.header)
        
                    if page.status_code != 200:
                        print("Unable to load webpage: {}. Status Code: {}".format(self.url+car,page.status_code))
                        continue
                    
                    page_soup = BeautifulSoup(page.content, 'html5lib')
                    
                    #- Check if page has a consumer ratings section. If not, remove 'review/' from URL and load new URL
                    consumer_section = list(page_soup.select('section.consumer-reviews'))
                    
                    if len(consumer_section)==0:
                        car = '/'.join(car.split('/')[:-2])
                        page = requests.get(self.url+car, headers=self.header)
                        
                        if page.status_code != 200:
                            print("Unable to load webpage: {}. Status Code: {}".format(self.url+car,page.status_code))
                            continue
        
                        page_soup = BeautifulSoup(page.content, 'html5lib')
        
                    
                    #print('{} {}'.format(page.status_code,self.url+car))    
                    print('.')
                    
                    #====== Scraping =======
                    #- Scorecard
                    scorecard = self.get_scorecard(page_soup)
                    #print(get_scorecard(page_soup))
                        
                    #- Consumer Ratings
                    consumer_overall, consumer_total, consumer_ratings = self.get_consumer_ratings(page_soup)
                    #print(get_consumer_ratings(page_soup))
                    
                    #- Pros and Cons
                    PROS, CONS = self.get_pro_con(page_soup)
                    #print(PROS)
                    #print(CONS)
                    
                    self.car_year.append(year)
                    
                    if body=='None':
                        self.car_model.append(' '.join([make, model]))
                    else:
                        self.car_model.append(' '.join([make, model, body]))
                    
                    self.car_model_num.append(model_num)
                    self.edmunds_overall.append(scorecard['overall'])
                    self.edmunds_driving.append(scorecard['driving'])
                    self.edmunds_comfort.append(scorecard['comfort'])
                    self.edmunds_interior.append(scorecard['interior'])
                    self.edmunds_utility.append(scorecard['utility'])
                    self.edmunds_technology.append(scorecard['technology'])
                    self.consumer_rating.append(consumer_overall)
                    self.consumer_total.append(consumer_total)
                    self.consumer_rating_5.append(consumer_ratings['5'])
                    self.consumer_rating_4.append(consumer_ratings['4'])
                    self.consumer_rating_3.append(consumer_ratings['3'])
                    self.consumer_rating_2.append(consumer_ratings['2'])
                    self.consumer_rating_1.append(consumer_ratings['1'])
                    self.pros1.append(PROS[0])
                    self.pros2.append(PROS[1])
                    self.pros3.append(PROS[2])
                    self.pros4.append(PROS[3])
                    self.cons1.append(CONS[0])
                    self.cons2.append(CONS[1])
                    self.cons3.append(CONS[2])
                    self.cons4.append(CONS[3])
                    
                except Exception:
                    print("An error was encountered while scraping data for {} {} {}".format(year, make, model))
                    print("Continuing to next car...")
                    traceback.print_exc(5)
                    continue

    def export_data(self, filename):
        edmunds = pd.DataFrame(
                {"car_year": self.car_year,
                 "car_model": self.car_model,
                 "model_number_new": self.car_model_num,
                 "Edmunds_overall": self.edmunds_overall,
                 "Edmunds_driving": self.edmunds_driving,
                 "Edmunds_comfort": self.edmunds_comfort,
                 "Edmunds_interior": self.edmunds_interior,
                 "Edmunds_utility": self.edmunds_utility,
                 "Edmunds_technology": self.edmunds_technology,
                 "Consumer_rating": self.consumer_rating,
                 "Consumer_total": self.consumer_total,
                 "Consumer_rating_5": self.consumer_rating_5,
                 "Consumer_rating_4": self.consumer_rating_4,
                 "Consumer_rating_3": self.consumer_rating_3,
                 "Consumer_rating_2": self.consumer_rating_2,
                 "Consumer_rating_1": self.consumer_rating_1,
                 "pros1": self.pros1,
                 "pros2": self.pros2,
                 "pros3": self.pros3,
                 "pros4": self.pros4,
                 "cons1": self.cons1,
                 "cons2": self.cons2,
                 "cons3": self.cons3,
                 "cons4": self.cons4})
        
        edmunds.to_excel(filename, sheet_name='edmunds', index=False)

#%%
if __name__ == '__main__':
    try:
        path = r'C:/Users/nholl/Dropbox/2019 FALL/GRA/Car Web Scraping/Testing/'
        os.chdir(path)

        crawl = Edmunds_Spider()
        
        crawl.get_scrape_dict('Model Numbers Assigned.xlsx')
        crawl.execute_scrape()
        crawl.export_data('Edmunds_WebScrape.xlsx')
    except:
        print("An error has occured. See traceback below: \n")
        print(traceback.print_exc(10))
        

