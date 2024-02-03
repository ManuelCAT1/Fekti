import base64
from Fekti import create_app
from flask_mail import Mail

app = create_app()


@app.template_filter('custom_b64encode')
def custom_b64encode(data):
    return base64.b64encode(data).decode('utf-8')

from flask import render_template

@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404


from Fekti.views import views
app.register_blueprint(views, name='my_views')


app.config['UPLOAD_FOLDER'] = '/photos/'


@app.template_filter('custom_b64encode')
def custom_b64encode_filter(value):
    if not isinstance(value, str):
        value = str(value)
    return base64.b64encode(value.encode('utf-8')).decode('utf-8')



if __name__ == '__main__':
    app.run()

























