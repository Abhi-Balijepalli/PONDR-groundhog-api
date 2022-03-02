# Required imports
# this container will be pushed onto the BETA launch.
# THIS WILL BE OPTIMIZED AFTER THE LAUNCH, AND THERE WILL BE MORE DOCUMENTATION.

import os
import tempfile
import openai

from flask import Flask, request, jsonify, render_template
from firebase_admin import credentials, firestore, initialize_app, auth, storage
from flask_cors import CORS, cross_origin
from datetime import datetime
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import *
# import ssl
# ssl._create_default_https_context = ssl._create_unverified_context

# Initialize Flask app
app = Flask(__name__)
CORS(app)
# Initialize Firestore DB
cred = credentials.Certificate('pondr-306720-firebase-adminsdk-eo52u-f50cb5da7b.json')
openai.api_key = ("")
default_app = initialize_app(cred, {'storageBucket': 'pondr-306720.appspot.com'})
sendgrid_client = SendGridAPIClient('')
db = firestore.client()
GPT3QA = db.collection('GPT3-QA')
REVIEW = db.collection('Posts')
PRODUCT = db.collection('Product')
COMPANY = db.collection('Companies')
LOGS = db.collection('Logs')
SUGGESTION = db.collection('Petitions')
CONSUMER_PRODUCTS = db.collection('ConsumerProducts')
ADVANCED_ANALYTICS = db.collection('Advanced_analytics')


def sendAnalyticsReadyEmail(company_id, productName, product_id):
    company_info = COMPANY.document(company_id).get().to_dict()
    message = Mail(
    from_email='no_reply@letspondr.com',
    to_emails=company_info['email'],
    html_content='<strong>and easy to do anywhere, even with Python</strong>')
    link = "https://www.letspondr.com/enterprise/product/productID=" + str(product_id)
    message.dynamic_template_data = {
        'report_link': link,
        'product_name': productName
    }
    message.template_id='d-c7659b07572b4e25abb3e0aa68211c93'
    try:
        response = sendgrid_client.send(message)
        print(response.status_code)
        print(response.body)
        print(response.headers)
    except Exception as e:
        print(e)
    

@app.route('/', methods=['GET'])
def Home():
    """
        Home(): The home page for the groundhog API
    """
    return "<b>Groundhog</b>"

def run_gpt_qa(form_id):
    """
        run_gpt_qa(form_id): Top 3 questions for GPT-3 Q&A on amazon deals of the day
        [Not an API Endpoint]
    """
    questions = ["What is the worst part about this product?","What do you like the most about this product?","Why would you buy this product again?"]
    answers = []
    for i in questions:
        response = openai.Answer.create(
            search_model="ada",
            model="curie",
            question=i,
            file=form_id,
            examples_context="In 2017, U.S. life expectancy was 78.6 years. With a 2019 population of 753,675, it is the largest city in both the state of Washington and the Pacific Northwest",
            examples=[["What is human life expectancy in the United States?", "78 years."],
                        ["what is the population of Seattle?", "Seattle's population is 724,305"]],
            max_tokens=40,
            stop=["\n", "<|endoftext|>"],
        )
        answers.append(str(response['answers']))
    return answers

@app.route('/asins', methods=['GET'])
def get_asin_numbers():
    """
       get_asin_numbers(): get all the asin numbers in our DB
    """
    try:
        documents = [doc.to_dict() for doc in CONSUMER_PRODUCTS.stream()]
        asins = []
        for i in documents:
            asins.append(i['asin'])
        return (jsonify({"IDs": asins}))
    except:
        return f"An error Occured: {e}"


@app.route('/consumer_product', methods=['POST'])
def add_consumer_product():
    """
       add_consumer_product(): post customer facing data.
    """
    try:
        data = request.json['data']
        key = data['key']
        if key == "(#z_3mhQ6xo[$B&":
            now = datetime.now()
            product_name = data['product_name']
            asin = data['asin']
            document = CONSUMER_PRODUCTS.add({
                'productName': product_name,
                'asin': asin
            })
            cp_document_ref = document[1]
            cp_doc_id = cp_document_ref.id

            cp_document_ref.update({
                'productID': cp_doc_id,
                u'dateCreated': now
            })

            advanced_analytics = {
                'productID': cp_doc_id,
                 u'dateCreated': now,
                '2': data['2'],
                '3': data['3'],
                '4': data['4'],
                '5': data['5'],
                '6': data['6'],
                'summary': data['summary'],
                'review_types': data['review_types']
            }
            
            gpt_3 = {
                'productID': cp_doc_id,
                 u'dateCreated': now,
                'gpt3_form_id': data['gpt3_form_id']
            }

            cp_document_ref.collection("Advanced_Analytics").document('0').set(advanced_analytics)
            cp_document_ref.collection("GPT3-QA").document('0').set(gpt_3)

            # Increments total # of products
            metrics_doc = LOGS.document('metrics').get().to_dict()
            LOGS.document('metrics').update({
                'consumer_products': metrics_doc['consumer_products'] + 1
            })

            return (jsonify({"documentID": str(cp_doc_id)}, 200))
        else:
            return ("You are not authorized to view this page"), 403
    except Exception as e:
        return f"An error Occured: {e}"

@app.route('/analyze', methods =['POST'])
def post_advanced_analytics():
    """
        post_advanced_analytics(): send processed reviews to basic analytics and advanced analytics.
    """
    now = datetime.now()
    try:
        data = request.json['data']
        if data['auth_key'] == "rJ8MBDy67q":
            product_name = data['product_name']
            company_id = data['company_id']
            product_id = data['product_id']
            path_on_cloud = "wordclouds/"+str(product_id)
            analytics_id = product_id
            graph1 = data['1']
            graph2 = data['2']
            graph3 = data['3']
            graph4 = data['4']
            graph5 = data['5']
            summary = data['summary'] #this includes other types of information such as net promoter score, GPT type...etc
            review_types = data['review_types']
            gpt_form = data['gpt3_form_id']
            date = str(datetime.timestamp(now))
            gpt3_qa_doc = GPT3QA.document(product_id)
            """
            Creating a GPT-3 Q/A document
            """
            gpt3_qa_doc.set({
                'product_id': product_id,
                'company_id': company_id,
                'date': date,
                'gpt3_form_id': gpt_form
            })
            today_date = str(datetime.date(now))
            
            """
            Creating a Advanced Analytics document
            """
            advanced_analytics_document = ADVANCED_ANALYTICS.document(analytics_id)
            advanced_analytics_document.set({
                'product_name': product_name,
                'company_id': company_id,
                'product_id': product_id,
                '1': graph1,
                '2': graph2,
                '3': graph3,
                '4': graph4,
                '5': graph5,
                'summary': summary,
                'Review-types': review_types,
                'word_cloud_path': path_on_cloud,
                'analytics_id': analytics_id,
                'gpt3_form_id': gpt_form
            })
            doc = PRODUCT.document(product_id) # doc is Document Reference
            field_updates = {"processed": True, "rescrape": False}
            doc.update(field_updates)
            sendAnalyticsReadyEmail(company_id, product_name, product_id)
            return jsonify({"success": True}), 200
    except Exception as e:
        return f"An Error Occured: {e}"

@app.route('/all-products', methods=['GET'])
def get_products():
    """
        get_products(): get all products in out DB
    """
    try:
        documents = [doc.to_dict() for doc in PRODUCT.stream()]
        return (jsonify({"All Products": documents}),200)
    except Exception as e:
        return f"An error Occured: {e}"

@app.route('/product/waitlist', methods=['GET'])
def get_products_waitlist():
    """
        get_products_waitlist(): Get all products that are yet to be analyzed.
    """
    try:
        query_ref = PRODUCT.where(u'processed', '==',False)
        query_ref_2 = PRODUCT.where(u'processed', '==', True).where(u'reanalyze','==', True)
        normal_waitlist = [doc.to_dict() for doc in query_ref.stream()]
        rescrape_waitlist = [doc.to_dict() for doc in query_ref_2.stream()]
        fifo =  normal_waitlist[::-1] + rescrape_waitlist[::-1]
        return (jsonify({"Products to be analyized": fifo}),200)
    except Exception as e:
        return f"An error has Occured: {e}"

@app.route('/product/waitlist/<id>', methods=['GET'])
def get_products_waitlist_by_company(id):
    """
        get_products_waitlist_by_company(id): Get all products that are yet to be analyzed by company ID.
    """
    try:
        query_ref = PRODUCT.where(u'processed', '==',False).where(u'Company_id', '==', id)
        documents = [doc.to_dict() for doc in query_ref.stream()]
        return (jsonify({"Products to be analyized": documents}),200)
    except Exception as e:
        return f"An error has Occured: {e}"


port = int(os.environ.get('PORT', 8080))
if __name__ == '__main__':
    # company_id = "3AhLUGn4EpNZct7MRV3wuWlErYS2"
    # product_name = "Gamer gorl bath water"
    # product_id = "69401234"
    # print(product_name)
    # sendAnalyticsReadyEmail(company_id, product_name, product_id)
    app.run(threaded=True, host='127.0.0.1', port=port, debug=True)
