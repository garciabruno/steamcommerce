#!/usr/bin/env python
# -*- coding:Utf-8 -*-

import json
import requests

from steamcommerce_api.core import models

PROVINCES = {
    'C': 'Ciudad Autonoma de Buenos Aires',
    'B': 'Buenos Aires',
    'K': 'Catamarca',
    'H': 'Chaco',
    'U': 'Chubut',
    'X': 'Cordoba',
    'W': 'Corrientes',
    'E': 'Entre Rios',
    'P': 'Formosa',
    'Y': 'Jujuy',
    'L': 'La Pampa',
    'F': 'La Rioja',
    'M': 'Mendoza',
    'N': 'Misiones',
    'Q': 'Neuquen',
    'R': 'Rio Negro',
    'A': 'Salta',
    'J': 'San Juan',
    'D': 'San Luis',
    'Z': 'Santa Cruz',
    'S': 'Santa Fe',
    'G': 'Santiago del Estero',
    'V': 'Tierra del Fuego',
    'T': 'Tucuman'
}

for key in PROVINCES.keys():
    print 'Populating province key %s (%s)' % (key, PROVINCES[key])

    province = models.Province()

    province.letter = key
    province.name = PROVINCES[key]

    commited = province.save()

    if commited:
        print 'Province with key %s saved' % key

    print 'Calling correoargentino.com.ar to get cities for %s' % key

    req = requests.post(
        'http://www.correoargentino.com.ar/sites/all/modules/custom/ca_forms/api/wsFacade.php',
        data={
            'action': 'localidades',
            'altura': '',
            'calle': '',
            'localidad': 'none',
            'provincia': key
        }
    )

    if req.status_code != 200:
        raise Exception('Did not receive 200')

    try:
        response = json.loads(req.text[1:])
    except:
        raise Exception('Could not serialize')

    print 'Populating cities for province key %s (%s)' % (key, PROVINCES[key])

    for city_data in response:
        city = models.City()

        city.province_letter = key
        city.internal_id = city_data['id']
        city.name = city_data['nombre']
        city.cp = city_data['cp']

        commited = city.save()

        if commited:
            print 'City name %s for province key %s saved' % (city_data['nombre'], key)

print 'Finished all population'
