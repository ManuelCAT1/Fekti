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




if __name__ == '__main__':
    app.run(port = 0000, debug=True)

























