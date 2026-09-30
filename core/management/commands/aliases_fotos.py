"""
Diccionario de aliases para fotos: {nombre_normalizado_en_archivo: 'nombre_empresa'}

⚠️ IMPORTANTE: las claves deben estar SIN acentos ni Ñ, porque
   la función normalizar() convierte 'ñ' → 'n' y quita tildes.
"""

ALIASES_FOTOS = {
    'juanantonioribera': 'Butifarras Lili',
    'gerardomadrigal': 'La Glorieta de la Jicara',
    'sandibeltaracena': 'Butifarras de Sandy',
    'marcoantoniomagana': 'Butifarras Marco Antonio',       # ← sin Ñ
    'mariajimenez': 'Yoko ixikob xalpan',
    'guadalupericardez': 'Butifarraslupita',
    'mariamaganalopez': 'Butifarras mary',                  # ← sin Ñ
    'juancarlosdominguez': 'Butifarras la Palapa del Biólogo',
    'ponchorocher': "D' Rocher",
    'pedroalejandroperezmondragon': 'Centro Botanero Niñon Jr',
    'juliocesaralamilla': 'Autoservicio Alamilla',
    'juanadejesushernandezhernandez': 'Yoko ixikob xalpan',
    'betolopez': 'Butifarras yuli',
    'yulianagomezlopez': 'Butifarras don Julián',
    'ranselmadrid': 'Butifarras ABI',
    'eduardocastillo': 'Butifarras y barbacoa don karina',
    'franciscaperez': 'Butifarras Doña Panchita',
    'teresagarcia': 'Butifarra Don Dago',
    'yeseniaizquierdo': 'Butifarras yesenia',
    'paolamtzmgal': 'Butifarras el Buen Sazón',
    'valeriaalamilla': 'Autoservicio Alamilla',
    'marcelaelviramedinaperez': 'El rincón de la abuelita',
    'normaalmeida': 'La Jalpanequita Butifarras',
    'irisjimenez': 'Butifarras el Buen Sazón',
    'luisalmeida': 'BUTIFARRAS EL SABOR DE JALPA',
    'rocioguadalupemadrigalmagana': 'La Glorieta de la Jicara',  # ← sin Ñ
    'nayeliguadalupevalenzuelagarcia': 'La Barra de Lite',
    'anagarcia': 'Butifarras Doña Anita',
    'mariaconcepcion': 'Centro Botanero Niñon Jr',
    'sebastianlopez': 'Tany Jr.',
}