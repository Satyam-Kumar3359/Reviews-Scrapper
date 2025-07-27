
from flask import Flask, render_template, request
from flask_cors import CORS, cross_origin
import requests
from bs4 import BeautifulSoup as bs
from urllib.request import urlopen as uReq
import logging

logging.basicConfig(filename="scrapper.log", level=logging.INFO)
import pymongo

app = Flask(__name__)

@app.route("/", methods=['GET'])
def homepage():
    return render_template("index.html")

@app.route("/review", methods=['POST', 'GET'])
def index():
    if request.method == 'POST':
        try:
            searchString = request.form['content'].replace(" ", "")
            flipkart_url = "https://www.flipkart.com/search?q=" + searchString
            uClient = uReq(flipkart_url)
            flipkartPage = uClient.read()
            uClient.close()

            flipkart_html = bs(flipkartPage, "html.parser")
            bigboxes = flipkart_html.find_all("div", {"class": "cPHDOP col-12-12"})

            if len(bigboxes) < 4:
                logging.info("No product boxes found")
                return "Product not found or Flipkart structure changed"

            del bigboxes[0:3]
            box = bigboxes[0]
            productLink = "https://www.flipkart.com" + box.div.div.div.a['href']

            prodRes = requests.get(productLink)
            prodRes.encoding = 'utf-8'
            prod_html = bs(prodRes.text, "html.parser")

            commentboxes = prod_html.find_all("div", {"class": "RcXBOT"})
            filename = searchString + ".csv"
            fw = open(filename, "w", encoding='utf-8')
            headers = "Product, Customer Name, Rating, Heading, Comment \n"
            fw.write(headers)
            reviews = []

            for commentbox in commentboxes:
                try:
                    name = commentbox.div.div.find_all("p", {"class": "_2NsDsF AwS1CA"})[0].text
                except Exception as e:
                    logging.info(f"name error: {e}")
                    name = "No Name"

                try:
                    rating = commentbox.div.div.div.div.text
                except Exception as e:
                    logging.info(f"rating error: {e}")
                    rating = "No Rating"

                try:
                    commentHead = commentbox.div.div.div.p.text
                except Exception as e:
                    logging.info(f"commentHead error: {e}")
                    commentHead = "No Comment Heading"

                # try:
                #     comtag = commentbox.div.div.find_all('div', {'class': ''})
                #     custComment = comtag[0].div.text if comtag and comtag.div else "Comment"
                #     # custComment = comtag[0].div.text
                # except Exception as e:
                #     logging.info(f"custComment error: {e}")
                #     custComment = "No Comment"
                try:
                    comment_container = commentbox.find("div", {"class": "ZmyHeo"})
                    if comment_container:
                        inner_div = comment_container.find("div")
                        custComment = inner_div.text.strip() if inner_div else "No Comment"
                    else:
                        custComment = "No Comment"
                except Exception as e:
                    logging.info(f"custComment error: {e}")
                    custComment = "No Comment"
                    
         #  ✅ Only append if actual comment is found
                if custComment == "No Comment" and name == "No Name" and rating == "No Rating" and commentHead == "No Comment Heading":
                    continue  # skip this commentbox
            

                mydict = {
                    "Product": searchString,
                    "Name": name,
                    "Rating": rating,
                    "CommentHead": commentHead,
                    "Comment": custComment
                }
                reviews.append(mydict)
                fw.write(f"{searchString},{name},{rating},{commentHead},{custComment}\n")
            fw.close()

            logging.info("log my final result {}".format(reviews))
            #mongodb se connection krna 
            client=pymongo.MongoClient("mongodb+srv://sk3823835:satyamkumar@cluster0.bccr1v3.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")
            db=client['review_scrapper']#db created
            review_collection=db['review_scrap_data']#collection is created inside the database
            review_collection.insert_many(reviews)

            return render_template('result.html', reviews=reviews[0:(len(reviews))])
        except Exception as e:
            logging.info(f"main error: {e}")
            return "Something went wrong. Please try again later."
    else:
        return render_template('index.html')

if __name__ == "__main__":
    app.run(port=5000)#host="0.0.0.0"



#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
