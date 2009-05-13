import os
import cgi
import couchquery
import webenv
import simplejson
import markdown
from mako.template import Template
from webenv.rest import RestApplication

this_directory = os.path.abspath(os.path.dirname(__file__))

db = couchquery.CouchDatabase("http://127.0.0.1:5984/ripannotations")
db.sync_design_doc("annotations", os.path.join(this_directory, 'design'))

admin_username, admin_password = open(os.path.join(this_directory, '.passwd')).read().split(':')
admin_password = admin_password.strip()

class Application(RestApplication):
    def GET(self, request, r=None):
        if r in ['index.html', 'credits.html']:
            return webenv.HtmlResponse(open(os.path.join(this_directory, r)).read())
        if r is None:
            return webenv.HtmlResponse(open(os.path.join(this_directory, 'index.html')).read())
        if r == 'get-annotations':
            time = float(request.query['time'])
            if time < 30:
                starttime = 0
            else:
                starttime = time - 30
            q = db.views.annotations.byStarttime(startkey=starttime, endkey=time)
            return webenv.JsonResponse([r for r in q.rows if r.endtime > time])
        if r == 'admin':
            a = db.views.annotations.byStarttime().rows
            t = Template(filename=os.path.join(this_directory, 'admin.mko'))
            return webenv.HtmlResponse(t.render(annotations=a))
        return webenv.Response404(r+' not found.')
        
    def POST(self, request, r):
        if r == 'add-annotation':
            entry = simplejson.loads(str(request.body))
            if entry['duration'] > 30:
                return webenv.Response403("Duration too long. 30 Second max.")
            entry['endtime'] = entry['starttime'] + entry['duration']
            assert type(entry['duration']) is int
            entry['starttime'] = float(entry['starttime'])
            entry['time'] = cgi.escape(entry['time'])
            entry['annotation'] = cgi.escape(entry['annotation'])
            entry['rendered'] = markdown.markdown(entry['annotation'])
            entry['type'] = 'annotation'
            s = db.create(entry)
            return webenv.Response201(simplejson.dumps(s))
            
    def DELETE(self, request, r, _id):
        if not request.query.has_key('username') or not request.query.has_key('password'):
            return webenv.Response404("Not admin.")
        if request.query['username'] == admin_username and request.query['password'] == admin_password:
            db.delete(db.get(_id));
            return webenv.Response()
        return webenv.Response404("Not admin.")


application = Application() 

if __name__ == "__main__":
    from wsgiref.simple_server import make_server
    httpd = make_server('', 8888, application)
    print "Serving on http://localhost:8888/"
    httpd.serve_forever()
