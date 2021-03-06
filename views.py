from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from django.core.urlresolvers import reverse#,resolve
#from django.contrib.auth.models import User
from django.utils.dateparse import parse_date
from django.contrib.auth.decorators import login_required

import datetime
import dateutil.parser
import functools
import collections

from apps.utils.decorators import t_login_required_ajax
from apps.utils.services import *
from apps.utils.utils import t_log
import settings
import apps.dashboard.settings
from apps.navigation import navigation

from apps.querystring_parser.querystring_parser import parser

#######################
# Views for dashboard
######################

# index : overall view for a given user
#               - activities table for that user
#               - collections associated with that user
#               - charts:
#                       - activity chart for that user (line, activities by time, activities==login/save/access/change)
#                       - status for aggregated pages in *all* users' collections (pie, new/inprogress/done/final)
#                       - bar... ?

# dashboard/index is the dashboard for that logged in user. Will show actions, collections and metrics for that user
@login_required
def index(request):
    t = request.user.tsdata.t
    
    last_actions = t.actions(request,{'nValues' : 5,  'userid': request.user.tsdata.userId, 'typeId': 4 })
    if isinstance(last_actions,HttpResponse):
        return apps.utils.views.error_view(request,last_actions)

    for la in last_actions :
         la['time'] = dateutil.parser.parse(la['time']).strftime("%a %b %d %Y %H:%M")

    action_types = t.actions_info(request)
    if isinstance(action_types,HttpResponse):
        return apps.utils.views.error_view(request,action_types)

#    oat = collections.OrderedDict(sorted(action_types))
#    myDic = action_types
#    sorted_list=sorted(myDic.items(), key=lambda x: x[0])
#    myOrdDic = OrderedDict(sorted_list)
#    return render(request, 'dashboard/homepage.html', {'action_types': myOrdDic, 'up': None, 'next': None, 'prev': None} )
    return render(request, 'dashboard/homepage.html', {'last_actions': last_actions, 'action_types': action_types, 'nav_up': None, 'nav_next': None, 'nav_prev': None} )


# dashboard/{colID}
# d_collection : overall view for a given collection
#               -tables
#                       - activities table for that collection
#                       - documents belonging to that collection
#                       - users associated with that collection
#               - charts:
#                       - activity chart for that collection (line, activities by time, activities==login/save/access/change)
#                       - status for aggregated pages in collection (pie, new/inprogress/done/final)
#                       - bar for top 5 users by activity

@login_required
def d_collection(request,collId):
    t = request.user.tsdata.t
 
    last_actions = t.actions(request,{'nValues' : 5, 'collId' : collId, 'userid': request.user.tsdata.userId, 'typeId': 4 })
    if isinstance(last_actions,HttpResponse):
        return apps.utils.views.error_view(request,last_actions)

    for la in last_actions :
         la['time'] = dateutil.parser.parse(la['time']).strftime("%a %b %d %Y %H:%M")

    #Avoid this sort of nonsense if possible
    collections = t.collections(request,{'end':None,'start':None})
    if isinstance(collections,HttpResponse):
        return apps.utils.views.error_view(request,collections)

    action_types = t.actions_info(request)
    if isinstance(action_types,HttpResponse):
        return apps.utils.views.error_view(request,action_types)

    navdata = navigation.get_nav(collections,collId,'colId','colName')
    #if we didn't have a focus before navigation call, we'll have one after
    collection = navdata.get("focus")
    pagedata = {'last_actions': last_actions, 'collection': collection, 'action_types': action_types}
    #merge the dictionaries
    combidata = pagedata.copy()
    combidata.update(navdata)

    return render(request, 'dashboard/collection.html', combidata)


# dashboard/{colID}/{docId}
# d_collection : overall view for a given collection
#               -tables
#                       - activities table for that document
#                       - pages belonging to that document as thumbs
#                       - users associated with that document (?collection)
#               - charts:
#                       - activity chart for that document (line, activities by time, activities==login/save/access/change)
#                       - status for aggregated pages in document (pie, new/inprogress/done/final)
#                       - bar for top 5 users by activity



@login_required
def d_document(request,collId,docId):
    t = request.user.tsdata.t

    last_actions = t.actions(request,{'nValues' : 5, 'collId' : collId, 'docId' : docId, 'userid': request.user.tsdata.userId, 'typeId': 4  })
    if isinstance(last_actions,HttpResponse):
        return apps.utils.views.error_view(request,last_actions)

    for la in last_actions :
         la['time'] = dateutil.parser.parse(la['time']).strftime("%a %b %d %Y %H:%M")

    documents = t.documents(request,{'collId': collId}) #for nav only...
    if isinstance(documents,HttpResponse):
        return apps.utils.views.error_view(request,documents)

    fulldoc = t.fulldoc(request,{'collId': collId, 'docId': docId})
    if isinstance(fulldoc,HttpResponse):
        return apps.utils.views.error_view(request,fulldoc)

    action_types = t.actions_info(request)
    if isinstance(action_types,HttpResponse):
        return apps.utils.views.error_view(request,action_types)

    document=None
    prev=None
    prev_content=None
    next=None
    next_content=None
    up_content=None
    stop_next=False
    for doc in documents:
        if stop_next:
            next=doc.get('docId')
            next_content=doc.get('title')
            break
        if doc.get("docId") == int(docId):
            document = doc
            stop_next=True
            for col in doc.get('collectionList').get('colList'):
                if(col.get('colId') == int(collId)):
                    up_content=col.get('colName')
                    up_id=col.get('colId')
                    break
        else :
            prev=doc.get('docId')
            prev_content=doc.get('title')

#    t_log("NEXT: %s PREV: %s UP: %s" % (next,prev,up))
#    t_log("REQPATH: %s" % (request.path))
#    t_log("RESOLVED %s" % (resolve(request.path)))
#    t_log("APP_NAME: %s" % (request.resolver_match.app_name))

    return render(request, 'dashboard/document.html', {'document': fulldoc.get('md'),
							'last_actions': last_actions,
                                                        'action_types': action_types,
							'nav_up_content': up_content,
							'nav_up_id': up_id,
							'nav_next': next, 
							'nav_next_content': next_content,
							'nav_prev':prev,
							'nav_prev_content': prev_content })


# dashboard{collId}/u/{username} is the dashboard for that user. Will show actions, collections and metrics for that user, can only be accessed by collection owners (editors?)
@login_required
def d_user(request,collId,username):
    t = request.user.tsdata.t
    # If the logged in user is owner of collection collId then (and username is a member)
    # Then we get relevant data about that user+collection and make dashboard view
    t_log("##################### USERNAME: %s " % username, logging.WARN)
    
    user = t.user(request,{'user' : username})
    if isinstance(user,HttpResponse):
        return apps.utils.views.error_view(request,user)

    t_log("##################### USER: %s " % user, logging.WARN)
    #TODO send userid param  with this request
    action_types = t.actions_info(request)
    if isinstance(action_types,HttpResponse):
        return apps.utils.views.error_view(request,action_types)

    return render(request, 'dashboard/user.html', {'action_types': action_types, 'user' : user} )


##########
# Helpers
##########

# paged_data:
#       - Handle common parameters for paging and filtering data
#       - Calls utils.services.t_[list_name] requests
#       - Some params must be passed in params (eg ids from url, typeId from calling function)
#       - Some params are set directly from REQUEST, but can be overridden by params (eg nValues)

def paged_data(request,list_name,params=None):#collId=None,docId=None):

    t = request.user.tsdata.t

    #collect params from request into dict
    dt_params = parser.parse(request.GET.urlencode())
#    t_log("DT PARAMS: %s" % dt_params)
    if params is None: params = {}
    params['start'] = str(dt_params.get('start_date')) if dt_params.get('start_date') else None
    params['end'] = str(dt_params.get('end_date')) if dt_params.get('end_date') else None
    params['index'] = int(dt_params.get('start')) if dt_params.get('start') else 0

    #NB dataTables uses length, transkribus nValues
    if 'nValues' not in params :
        params['nValues'] = int(dt_params.get('length')) if dt_params.get('length') else settings.PAGE_SIZE_DEFAULT

#    params['sortColumn'] = int(dt_params.get('length')) if dt_params.get('length') else None
#    params['sortDirection'] = int(dt_params.get('start')) if dt_params.get('start') else None

    #this is the way that datatables passes things in when redrawing... may do something simpler for filtering if possible!!
    if 'columns' in dt_params and list_name == "actions" and dt_params.get('columns').get(5).get('search').get('value'):
        params['typeId'] = int(dt_params.get('columns').get(5).get('search').get('value'))

    ########### EXCEPTION ############
    # docId is known as id when passed into actions/list as a parameter
    if  list_name == 'actions' : params['id'] = params['docId']
    ##################################

    #Get data
    data=None
    t_log("SENT PARAMS: %s" % params)
    data = eval("t."+list_name+"(request,params)")

    #Get count
    count=None
    #When we call a full doc we *probably* want to count the pages (we can't fo that with a /count call)
    if list_name not in ["fulldoc"]:
        count = eval("t."+list_name+"_count(request,params)")
    #In some cases we can derive count from data (eg pages from fulldoc)
    if list_name == "fulldoc" : #as we have the full page list in full doc for now we can use it for a recordsTotal
        count = data.get('md').get('nrOfPages')

    return (data,count)

##### Views for chart data #######

# actions_for_chart_ajax
#       - sends nValues=-1 to get all data available
#       - prepares datasets against time
#       - TODO we'll need an entry for regular time intervals to reflect activity properly

@t_login_required_ajax
def chart_ajax(request,list_name,chart_type,collId=None,docId=None,userId=None,subject=None,label=None) :

    # When requesting data for chart we do not want this paged so nValues=-1
    # Other constraint params can be used (ids, dates etc)
    (data,count) = paged_data(request,list_name,{'nValues':-1, 'collId': collId, 'docId': docId, 'userid': userId})

    if isinstance(data,HttpResponse):
        t_log("%s failed" % t_list_name,logging.WARN)
        return apps.utils.views.error_view(request,data)

    if data is None: #No data? we send a 404
        HttpResponse('Not found', status=404)

    return eval(chart_type+"(data,subject,label)")

#plot bar for the X number of Y with greatest number of (activity) records
def top_bar(data,subject,label=None,chart_size=None):

    #map just the users to list
#    just_subject = list(set(isolate_data(data,'userName')))
#    just_userids = list(set(isolate_data(data,'userId')))

#    t_log("JUST_SUBJECT: %s" % just_subject)
    if chart_size is None : chart_size = settings.PAGE_SIZE_DEFAULT
    t_log("*subject: %s label: %s" % (subject,label))

    actions = {}
    labels = {}
    for datum in data:
        subject_value = datum.get(subject)
        if subject_value is None : continue

        #we can maintain labels separate to subjects 
        # (eg we can use colId to key/sort data and colName when displaying... protects agains duplicate colNames cumulating
        label_value = datum.get(label)
        if subject_value not in labels and label_value is not None:
            labels[subject_value] = label_value
        #use subject value in case there is no value for the label
        if label_value is None: 
            labels[subject_value] = subject_value

        #accumulate the data
        if subject_value not in actions :
            actions[subject_value]=0
        else:
            actions[subject_value]+=1

    action_data = list(actions.values())
    key_data = list(actions.keys())

    chart_data=[]
    chart_labels=[]
    chart_label_ids=[]
    #This bit will retrun the index of the 5/chart_size subjects with the highest value in actions_data
    ind_arr = sorted(range(len(action_data)), key=lambda i: action_data[i], reverse=True)[:chart_size]
    for ind in ind_arr : 
        chart_data.append(action_data[ind])
        chart_labels.append(labels[key_data[ind]])
        chart_label_ids.append(key_data[ind])


    #TODO dynamically process colours...
    return JsonResponse({
            'labels': chart_labels,	
	    'label_ids': chart_label_ids,
            'datasets' : [{
		 #      'label' : "Top users by activity",
		       'borderWidth': 1,
		       'backgroundColor': [
				'rgba(255, 99, 132, 0.2)',
				'rgba(54, 162, 235, 0.2)',
				'rgba(255, 206, 86, 0.2)',
				'rgba(75, 192, 192, 0.2)',
				'rgba(153, 102, 255, 0.2)',
			    ],
			'borderColor': [
				'rgba(255,99,132,1)',
				'rgba(54, 162, 235, 1)',
				'rgba(255, 206, 86, 1)',
				'rgba(75, 192, 192, 1)',
				'rgba(153, 102, 255, 1)',
			    ],
            	       'data': chart_data,
			}]
        },safe=False)


#plot the (activites) data against time as a line
#subject and label not used here (yet)
def line(data,subject=None,label=None):
    
    action_info = {
                  1 : {'label' : 'Save' ,'colour': 'rgba(255,99,132,1)'},
                  2 : {'label' : 'Login', 'colour': 'rgba(54, 162, 235, 1)'},
                  3 : {'label' : 'Status change' , 'colour' :'rgba(255, 206, 86, 1)'},
                  4 : {'label' : 'Access document', 'colour' : 'rgba(75, 192, 192, 1)'},
                }
    if(len(data) == 0) :
        return JsonResponse({'labels': [],'datasets' : []},safe=False)

    #map just the times to list
    just_times = isolate_data(data,'time')
    just_types = list(set(isolate_data(data,'typeId'))) #unique types

    #get max and min
    max_time = max(just_times)
    min_time = min(just_times)
    #start, end and delta
    d = dateutil.parser.parse(min_time).date()
    end = dateutil.parser.parse(max_time).date()
    day = datetime.timedelta(days=1)
    #off we go...
    x_data = {}
    types = {}
    #make a dict with a record for each day and the day as the key
    while d <= end:
        x_data[d] = 0
        d = d+day

    #assign each dataset (type) an x_data array
    #we cound use the actions_info data hardcoded above
    #but that would miss any types we weren't aware of
    while just_types:
        type_id =just_types.pop()
        types[type_id] = x_data.copy()
    #fill in null cases TODO merge this wirh above
    for type_id in action_info:
        if type_id not in types:
            types[type_id] = x_data.copy()

    #assign/increment values based on actions, we do this by type_id to the types dict
    for datum in data:
        d = dateutil.parser.parse(datum.get("time")).date()
        type_id = datum.get("typeId")
        if d in types[type_id] : types[type_id][d] = types[type_id][d]+1

    #now we put shake it all out into datasets for chart.js
    datasets = []
    for x in types:
        #order the dict by key (ie date) using collections.OrderedDict
        od = collections.OrderedDict(sorted(types.get(x).items()))
        datasets.append({
                         'data': list(od.values()),
                         'label': action_info.get(x).get('label'),
                         'fill': False,
                         'borderColor': action_info.get(x).get('colour'),
                         'backgroundColor': action_info.get(x).get('colour'),
                         'pointRadius': 0,
                         'pointHoverRadius': 5,
                         })

    return JsonResponse({
            'labels':  sorted(list(x_data.keys())),
            'datasets' : datasets
        },safe=False)

'''
def doughnut(data,subject=None,label=None):
    var ctx = document.getElementById("status_pie")
var myChart = new Chart(ctx, {
    type: 'doughnut',
    data: {
        labels: ["New", "In progress", "Complete", "Published"],
        datasets: [{
            label: 'Status',
            data: [12, 19, 3, 5],
            backgroundColor: [
                'rgba(255, 99, 132, 0.2)',
                'rgba(54, 162, 235, 0.2)',
                'rgba(255, 206, 86, 0.2)',
                'rgba(75, 192, 192, 0.2)',
            ],
            borderColor: [
                'rgba(255,99,132,1)',
                'rgba(54, 162, 235, 1)',
                'rgba(255, 206, 86, 1)',
                'rgba(75, 192, 192, 1)',
            ],
            borderWidth: 1
        }]
    },
    options: {
	 title: {
		    display: true,
		    text: 'Document statuses'
		}
    }
});
'''
def isolate_data(data,field) :
    return [d.get(field) for d in data]
##    return map(functools.partial(get_item, f=field), data)
##
##I would do this anonymously in map, but not sure how...
##def get_item(x,f) :
##    return x.get(f)


def filter_data(fields, data) :

    #data tables requires a specific set of table columns so we filter down the actions
    filtered = []
    #I suspect some combination of filter/lambda etc could do this better...
    for datum in data:
        filtered_datum = {}
        for field in fields :
            filtered_datum[field] = datum.get(field) if datum.get(field) else "n/a" #TODO this will n/a 0!!
        filtered.append(filtered_datum)

    return filtered

