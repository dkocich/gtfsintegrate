import json
import os

import requests
from conversionapp.models import Correspondence, ExtraField, Correspondence_Route, Correspondence_Agency
from django.db import connection
from django.shortcuts import render
from gs.forms import Correspondence_Route_Form, Correspondence_Agency_Form
from gs.tasks import save_comp, connect_to_JOSM_using_link, connect_to_JOSM_using_file, get_itineraries, \
    save_single_comp
from multigtfs.models import Stop, Feed, Route
from requests import post
import webbrowser
from osmapp import OSM_MapLayer

from .models import CMP_Stop
from .models import Relation_data
import uuid

from urllib.parse import urlencode

from . import data


def showmap_with_comp(request, pk):
    context = {
        'type': 'conversion_view',
        'feed_id': pk,
        'feed_name': Feed.objects.get(id=pk).name,
        'error': 'No errors'
    }

    # 1. Load all stops first
    try:
        stops = Stop.objects.filter(feed=pk)
    except Exception as e:
        context['error'] = 'No stops present'

    # Initially comparison should be done by the user
    try:
        for stop in stops:
            # osm_nodes_in_bound = get_nodes_within100m(str(stop.lon),str(stop.lat))
            if not CMP_Stop.objects.filter(gtfs_stop=stop).exists():
                comp_stop = CMP_Stop.objects.create(gtfs_stop=stop)
                comp_stop.save()
    except Exception as e:
        context['error'] = e

    return render(request, 'gs/comparison.html', {'context': context})


def create_stop(request):
    if request.method == 'POST':
        data_json = request.POST.get('data_to_match')
        data = json.loads(data_json)
        feed_id = data[0]['feed_id']
        gtfs_stop_data = data[0]['gtfs']
        lat = data[0]['lat']
        lon = data[0]['lon']
        print(gtfs_stop_data)

        generator = 'Python Script'
        outputparams = {
            'newline': '\n',
            'indent': '  ',
            'generator': " generator='{}'".format(generator)
        }

        name = gtfs_stop_data['name'].replace('&', '&amp;').replace("'", "&apos;").replace("<", "&lt;").replace(">",
                                                                                                                "&gt;").replace(
            '"', "&quot;")

        xml = "<?xml version='1.0' encoding='UTF-8'?>{newline}<osm version='0.6'{generator}>{newline}".format(
            **outputparams)

        xml += ('<node action="modify" id="-1" visible="True" incomplete="False" lat="{longitude}" lon="{latitude}" >'
                '{newline}{indent}<tag  k="public_transport" v="platform" />'
                '{newline}{indent}<tag k="bus" v="yes" />'
                '{newline}{indent}<tag k="name" v="{stop_name}" />'
                '{newline}{indent}<tag k="ref" v="{ref_value}" />'
                '{newline}</node>{newline}</osm>'.format(latitude=str(lon), longitude=str(lat), stop_name=name,
                                                         ref_value=str(gtfs_stop_data['stop_id']), **outputparams))

        connect_to_JOSM_using_file(xml)
        '''link = "http://localhost:8111/add_node?lon=" + str(lon) + "&lat=" + str(lat) + "&addtags=name=" + \
               name + "|ref=" + str(gtfs_stop_data['stop_id'])
        webbrowser.open(urlencode(link))'''

        return render(request, 'gs/comparison.html')


def match_stop(request):
    if request.method == 'POST':
        context = {
            'match_success': 0,
            'error': ''
        }

        data_to_match_json = request.POST.get('data_to_match')
        data_to_match = json.loads(data_to_match_json)
        print(data_to_match)

        feed_id = data_to_match[0]['feed_id']
        gtfs_stop_data = data_to_match[0]['gtfs']
        osm_stop_data = data_to_match[0]['osm']

        generator = 'Python Script'
        outputparams = {
            'newline': '\n',
            'indent': '  ',
            'generator': " generator='{}'".format(generator)
        }

        xml = '''<?xml version='1.0' encoding='UTF-8'?>{newline}<osm version='0.6'{generator}>{newline}'''.format(
            **outputparams)
        xml += save_single_comp(gtfs_stop_data, osm_stop_data, feed_id, stops_layer=False)
        xml += '''{newline}</osm>'''.format(**outputparams)

        values = {'data': xml, 'new_layer': 'true'}

        connect_to_JOSM_using_file(xml)

        print(xml)

    return render(request, 'gs/comparison.html')


def match_stops(request):
    if request.method == 'POST':
        context = {
            'match_success': 0,
            'error': ''
        }
        data_to_match_json = request.POST.get('data_to_match')
        data_to_match = json.loads(data_to_match_json)

        print(data_to_match)

        generator = 'Python Script'
        outputparams = {
            'newline': '',
            'indent': '',
            'upload': '',
            'generator': " generator='{}'".format(generator)
        }
        xml = '''<?xml version='1.0' encoding='UTF-8' ?>{newline}<osm version='0.6'{generator}>{newline}'''.format(
            **outputparams)
        for i in range(0, len(data_to_match)):
            feed_id = data_to_match[i]['feed_id']
            gtfs_stop_data = data_to_match[i]['gtfs']
            osm_stop_data = data_to_match[i]['osm']
            xml += save_single_comp(gtfs_stop_data, osm_stop_data, feed_id, stops_layer=True)

        xml += '''{newline}</osm>'''.format(**outputparams)

        connect_to_JOSM_using_file(xml)

    return render(request, 'gs/comparison.html', {'context': context})


def define_relation(request, pk=None):
    if request.method == "POST":
        route_form = Correspondence_Route_Form(request.POST)

        if route_form.is_valid():
            entered_route_corr_form = route_form.save(commit=False)
            entered_route_corr_form_feed_id = entered_route_corr_form.feed_id

            if Correspondence_Route.objects.filter(feed_id=entered_route_corr_form_feed_id).exists():
                print("Saving Route form")
            else:
                entered_route_corr_form.save()
    else:
        corr_form = Correspondence.objects.get(feed_id=pk)
        print(corr_form)

        context = {
            'feed_id': pk,
            'extra_data': '',
            'extra_data_ex': ''
        }

        extra_field_keys = []
        extra_data_ex = {}
        feed_routes = Route.objects.filter(feed=pk)
        print(feed_routes.all()[0].extra_data)
        ExtraField.objects.filter(feed_id=pk).all().delete()
        for i in range(0, len(feed_routes)):
            extra_data = feed_routes[i].extra_data
            for key, value in extra_data.items():
                if key not in extra_field_keys:
                    extra_field_keys.append(key)
                    if ExtraField.objects.filter(feed_id=pk, field_name=key, value=None).exists():
                        ef = ExtraField.objects.filter(feed_id=pk, field_name=key, value=None)[0]
                    else:
                        ef = ExtraField(feed_id=pk, field_name=key)
                        ef.save()
        context['extra_field_ex'] = extra_data_ex
        context['extra_field_keys'] = extra_field_keys
        route_form = Correspondence_Route_Form()
        return render(request, 'gs/define-relation.html',
                      {'context': context, 'route_form': route_form})


def save_route_corr(request):
    if request.method == "POST":
        route_form = Correspondence_Route_Form(request.POST)
        entered_route_corr_form_feed_id = -1
        if route_form.is_valid():
            entered_route_corr_form = route_form.save(commit=False)
            entered_route_corr_form_feed_id = entered_route_corr_form.feed_id
            context = {
                'feed_id': entered_route_corr_form_feed_id
            }
            if Correspondence_Route.objects.filter(feed_id=entered_route_corr_form_feed_id).exists():
                route_corr_obj = Correspondence_Route.objects.get(feed_id=entered_route_corr_form_feed_id)
                route_corr_obj.route_id = entered_route_corr_form.route_id
                route_corr_obj.agency = entered_route_corr_form.agency
                route_corr_obj.short_name = entered_route_corr_form.short_name
                route_corr_obj.long_name = entered_route_corr_form.long_name
                route_corr_obj.desc = entered_route_corr_form.desc
                route_corr_obj.rtype = entered_route_corr_form.rtype
                route_corr_obj.url = entered_route_corr_form.url
                route_corr_obj.color = entered_route_corr_form.color
                route_corr_obj.text_color = entered_route_corr_form.text_color

                route_corr_obj.save()
            else:
                entered_route_corr_form.save()

        else:
            print("Route form not valid {}".format(route_form))

        agency_form = Correspondence_Agency_Form()
        return render(request, 'gs/define-relation.html', {'context': context, 'agency_form': agency_form})


def save_ag_corr(request):
    if request.method == "POST":
        context = {
            'feed_id': -1
        }
        agency_form = Correspondence_Agency_Form(request.POST)

        if agency_form.is_valid():
            entered_agency_corr_form = agency_form.save(commit=False)
            entered_agency_corr_form_feed_id = entered_agency_corr_form.feed_id

            if Correspondence_Agency.objects.filter(feed_id=entered_agency_corr_form_feed_id).exists():
                ag_corr_obj = Correspondence_Agency.objects.get(feed_id=entered_agency_corr_form_feed_id)
                ag_corr_obj.feed_id = entered_agency_corr_form_feed_id
                ag_corr_obj.agency_name = entered_agency_corr_form.agency_name
                ag_corr_obj.agency_id = entered_agency_corr_form.agency_id
                ag_corr_obj.agency_url = entered_agency_corr_form.agency_url
                ag_corr_obj.agency_timezone = entered_agency_corr_form.agency_timezone
                ag_corr_obj.agency_lang = entered_agency_corr_form.agency_lang
                ag_corr_obj.agency_phone = entered_agency_corr_form.agency_phone
                ag_corr_obj.agency_fare_url = entered_agency_corr_form.agency_fare_url

                ag_corr_obj.save()
            else:
                entered_agency_corr_form.save()

            '''Creating XML File'''
            # get the routes form with that feed
            routes_list = Route.objects.filter(feed=entered_agency_corr_form_feed_id)
            routes_form = Correspondence_Route.objects.get(feed_id=entered_agency_corr_form_feed_id)

            valid_routes_attr_list = {}
            long_names_list = []
            short_names_list = []
            route_ids_db = []
            routes_data = {}
            extra_data_present = False
            extra_data = routes_form.extra_data.all()
            form_extra_data = {}
            form_extra_data_values = []
            if extra_data.count() > 0:
                extra_data_present = True

            if extra_data_present:
                for key in extra_data:
                    form_extra_data.update({key.field_name: key.value})
            print(form_extra_data)
            for key, value in routes_form.__dict__.items():
                if key == '_state':
                    continue
                elif key == 'feed_id':
                    continue
                else:
                    if value != '':
                        pair = {key: value}
                        valid_routes_attr_list.update(pair)

            print(valid_routes_attr_list)
            xml = ''

            choices = {
                '0': 'Tram, Streetcar, or Light rail',
                '1': 'Subway or Metro',
                '2': 'rail',
                '3': 'bus',
                '4': 'ferry',
                '5': 'Cable Car',
                '6': 'Godola or Suspended cable car',
                '7': 'Funicular'
            }

            for route in routes_list:
                xml += "\n<tag k='type' v='route_master'>\n"
                build_route_data = {}
                for r_key, r_value in route.__dict__.items():

                    if r_key == 'id':
                        route_ids_db.append(r_value)
                    if r_key == 'long_name':
                        val = r_value.replace('"', '')
                        long_names_list.append(val)
                    elif r_key == 'short_name':
                        sval = r_value.replace('"', '')
                        short_names_list.append(sval)
                    elif r_key == 'extra_data':
                        extra_data_json = r_value

                        if extra_data_present:
                            for ekey, evalue in extra_data_json.items():
                                xml += "<tag k='" + str(form_extra_data[ekey]) + "' v='" + str(evalue) + "' />\n"

                    if r_key in valid_routes_attr_list:
                        tag_key = valid_routes_attr_list[r_key]
                        if tag_key == 'colour' or tag_key == 'text_colour':
                            tag_val = '#' + r_value
                        elif r_key == 'rtype':
                            tag_val = choices[str(r_value)]
                        else:
                            tag_val = r_value

                        if tag_val != '' and str(tag_key) != 'None' and r_key != 'id':
                            xml += "<tag k='" + str(tag_key) + "' v='" + str(tag_val) + "' />\n"

            print(xml)

            complete_data = []

            if '' in long_names_list:
                if '' in short_names_list:
                    for i in range(0, long_names_list):
                        long_names_list[i] = 'line ' + str(i)
                else:
                    long_names_list = short_names_list

            for (route_id, name) in zip(route_ids_db, long_names_list):
                data = {"id": route_id, "name": name}
                routes_data[route_id] = name

            for i in range(0, len(route_ids_db)):
                if i == 0:
                    complete_data.append(get_itineraries(route_ids_db[i], entered_agency_corr_form_feed_id, start=True))
                else:
                    complete_data.append(
                        get_itineraries(route_ids_db[i], entered_agency_corr_form_feed_id, start=False))

            context['complete_data'] = json.dumps(complete_data)
            context['feed_id'] = entered_agency_corr_form_feed_id
            context['routes_data'] = json.dumps(routes_data)
        return render(request, 'gs/saved_relation.html', {'context': context, 'agency_form': agency_form})


def saveextra(request):
    if request.method == 'POST':
        in_feed_id = request.POST['feed_id']
        key = request.POST['key']
        val = request.POST['val']

        extrafield = ExtraField.objects.get(feed_id=in_feed_id, field_name=key, value=None)
        extrafield.value = val
        extrafield.save()

        route_form = Correspondence_Route.objects.get(feed_id=in_feed_id)
        route_form.extra_data.add(extrafield)

        print('{} {} {}'.format(in_feed_id, key, val))
        print(ExtraField.objects.filter(feed_id=in_feed_id, field_name=key).count())
    return render(request, 'gs/define-relation.html')


def equalizer(data):
    largest_length = 0  # To define the largest length

    for l in data:
        if len(l) > largest_length:
            largest_length = len(l)  # Will define the largest length in data.

    for i, l in enumerate(data):
        if len(l) < largest_length:
            remainder = largest_length - len(l)  # Difference of length of particular list and largest length
            data[i].extend([None for i in range(remainder)])  # Add None through the largest length limit

    return data


def download_relation(request):
    if request.method == 'POST':
        feed_id = request.POST.get('feed_id')
        token = request.POST.get('token')

        context = {
            'feed_id': feed_id
        }
        top_right = [float(request.POST.get('northeast_lon')), float(request.POST.get('northeast_lat'))]
        bottom_left = [float(request.POST.get('southwest_lon')), float(request.POST.get('southwest_lat'))]
        bbox = [bottom_left[1], bottom_left[0], top_right[1], top_right[0]]
        bbox_query = "bbox: " + str(bottom_left[1]) + ", " + str(bottom_left[0]) + ", " + str(
            top_right[1]) + ", " + str(top_right[0])
        query = '''
            [out:xml][timeout:100][''' + bbox_query + '''];
            (
             relation["route"="bus"];
            );
            (._;>;);
            out meta;
        '''

        print("Relation Query {}".format(query))
        try:
            result = post("http://overpass-api.de/api/interpreter", query)
        except ConnectionError as ce:
            context['connection_error'] = "There is a connection error while downloading the OSM data"

        PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
        xmlfiledir = xmlfiledir = os.path.join(os.path.dirname(PROJECT_ROOT), 'osmapp', 'static')
        xmlfile = xmlfiledir + '/relation.osm'

        with open(xmlfile, 'wb') as fh:
            fh.write(result.content)
        print("Data copied to xml")
        nodes_ids, relation_ids, relations_info, way_ids = load(xmlfile, feed_id, 'comp_relation')
        equalized_relation_info = equalizer(relations_info)
        Relation_data.objects.create(token=token, nodes_ids=nodes_ids,
                                     rels_ids=relation_ids,
                                     relations_info=equalized_relation_info, ways_ids=way_ids)

    return render(request, 'gs/saved_relation.html', {'context': context})


def match_relations(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.POST.get('data'))
        except Exception as e:
            print('******ERROR {} *****'.format(e))

        # get all the data of clicked lines relation
        token = request.POST.get('token')
        relation_data_obj = Relation_data.objects.get(token=token)
        ways = relation_data_obj.ways_ids
        nodes = relation_data_obj.nodes_ids

        all_relations_ids = relation_data_obj.rels_ids
        all_relations_data = {}

        # prepare data for all relations as a dict will rel id as key and data as value
        try:
            for i in range(0, len(all_relations_ids)):
                rel_id = all_relations_ids[i]
                ar = []

                for j in range(0, len(data)):
                    if rel_id == int(data[j][0]):
                        stop_names = []
                        for stop in data[j][2]:
                            # stop[1] = stop_name stop[2] = stop lat stops[3] = stop lon
                            stop_ar = [stop[1], stop[2], stop[3]]
                            stop_names.append(stop_ar)
                        ar = stop_names
                all_relations_data.update({rel_id: ar})

        except Exception as e:
            print('****** ERROR {} *****'.format(e))

        # create a maplayer and add nodes,ways and relations to MapLayer
        maplayer = OSM_MapLayer.MapLayer()
        maplayer.nodes = nodes
        maplayer.ways = ways
        maplayer.relations = all_relations_data

        # get xml
        xml = maplayer.to_xml()

        # connect to JOSM using file
        PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
        xmlfiledir = os.path.join(os.path.dirname(PROJECT_ROOT), 'osmapp', 'static')
        xmlfile = xmlfiledir + '/xmltojosm_' + str(uuid.uuid4()) + '.osm'

        with open(xmlfile, 'w') as fh:
            fh.write(xml)

        try:
            josm_url = 'http://localhost:8111/open_file?filename=' + xmlfile
            webbrowser.open(josm_url)
        except requests.exceptions.RequestException as e:
            context['error'] += 'JOSM not open {}'.format(e)
            print(e)

    return render(request, 'gs/saved_relation.html')
