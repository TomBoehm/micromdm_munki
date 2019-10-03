#!/usr/bin/python

import datetime
import requests
import json
import plistlib
import os.path
import urllib
import uuid

"""
    SETTINGS
"""
munkiFolder='/var/lib/nethserver/vhost/munki.ixpert.at'
icon_location=munkiFolder+"/icons_/"
vpp_apps_location=munkiFolder+"/pkgsinfo/apps/VPP/"
apiURL='https://munki.ixpert.at/micromdm/api.py'
tokenLoc='/home/micromdm/VPP/sToken_for_micromdm.vpptoken'
hostname='https://munki.ixpert.at'


"""
    FUNCTIONS
"""
def readFile(fileLocation):
    try:
        file = open(fileLocation, "r")
        fileContent= file.read()
        file.close()
        return fileContent
    except Exception, e:
        print "ERROR: Could not read " + fileLocation

def preinstall_script(appName,appVersion,appID):
    return """#!/bin/bash
appName='"""+appName+"""'
appVersion='"""+appVersion+"""'
appID="""+appID+"""
seriennummer=$( system_profiler SPHardwareDataType | grep \'Serial Number (system)\' | awk \'{print $NF}\' )
curl \""""+apiURL+"""?seriennummer=$seriennummer&appid=$appID&action=installApp"
exit 0"""

def uninstall_script(appName,appVersion,appID):
    return """"#!/bin/bash
appName='"""+appName+"""'
appVersion='"""+appVersion+"""'
appID="""+appID+"""
rm -R "/Applications/${appName}.app"
seriennummer=$( system_profiler SPHardwareDataType | grep \'Serial Number (system)\' | awk \'{print $NF}\' )
curl \""""+apiURL+"""?seriennummer=$seriennummer&appid=$appID&action=removeApp"
exit 0"""

def installcheck_script(appName,appVersion,appID):
    return """#!/bin/bash
appName='"""+appName+"""'
appVersion='"""+appVersion+"""'
appID="""+appID+"""
if [ -d "/Applications/${appName}.app" ]; then
    installedVersion=$( defaults read "/Applications/${appName}.app/Contents/Info.plist" CFBundleShortVersionString )
    # geogebra fix
    if [ "${appName}" == "GeoGebra Classic 6" ] || [ "${appName}" == "GeoGebra Geometry" ] || [ "${appName}" == "GeoGebra Graphing Calculator" ] ; then
        installedVersion="${installedVersion}.0"
    fi
    if [ "$installedVersion" == "$appVersion" ]; then
        exit 1
    fi
fi
exit 0"""

def readFile(fileLocation):
    try:
        file = open(fileLocation, "r")
        fileContent= file.read()
        file.close()
        return fileContent
    except Exception, e:
        print "ERROR: Could not read " + fileLocation

def getNameOfApp(appid) :
    appInfo=requests.get("https://uclient-api.itunes.apple.com/WebObjects/MZStorePlatform.woa/wa/lookup?version=2&id="+appid+"&p=mdm-lockup&caller=MDM&platform=enterprisestore&cc=at&l=de").content
    try:
        return json.loads(appInfo)["results"][appid]["name"]
    except:
        return ""

def updateEineApp(appid) :
    default_pkginfo={
        'autoremove': False,
        'unattended_install': True,
        'uninstallable': True,
        'unattended_uninstall': True,
        'installer_type': 'nopkg',
        'minimum_os_version': '10.4.0',
        'catalogs': ['testing'],
        'uninstall_method': 'uninstall_script',
        '_metadata': {
            'munki_version': '',
            'os_version': '',
            'created_by': 'tom',
            'creation_date': ''},
        'name': '',
        'description': '',
        'icon_name': '',
        'category': '',
        'developer': '',
        'version': '',
        'uninstall_script': '',
        'preinstall_script': '',
        'installcheck_script': '',
        }
    appInfo=requests.get("https://uclient-api.itunes.apple.com/WebObjects/MZStorePlatform.woa/wa/lookup?version=2&id="+appid+"&p=mdm-lockup&caller=MDM&platform=enterprisestore&cc=at&l=de").content
    appInfo=json.loads(appInfo)
    appName = getNameOfApp(appid)

    try:        # falls kein result retour kommt
        kind=appInfo["results"][appid]["kind"]
    except:
        return
    if kind != "desktopApp":
        return
    appVersion=appInfo["results"][appid]["offers"][0]["version"]["display"]
    try:
        myInfo=plistlib.readPlist(vpp_apps_location+appName+".plist")
    except:
      myInfo=default_pkginfo

    if ( myInfo["version"] != appVersion ):
        print "update"
        appDeveloper=appInfo["results"][appid]["artistName"]
        appDescription=appInfo["results"][appid]["description"]["standard"]
        app_category=appInfo["results"][appid]["genres"][0]["name"]
        app_minimum_os_version=appInfo["results"][appid]["minimumOSVersion"]
        # download Icon
        appName=appInfo["results"][appid]["name"]
        if ( os.path.exists(icon_location+appName+".png") == False ) :
            appUrl=appInfo["results"][appid]["artwork"]["url"].replace("{w}x{h}bb.{f}", "434x0w.png")
            urllib.urlretrieve (appUrl, icon_location+appName+".png")
        myInfo["name"] = appName
        myInfo["icon_name"] = appName+".png"
        myInfo["description"] = appDescription
        myInfo["developer"] = appDeveloper
        myInfo["version"] = appVersion
        myInfo["category"] = app_category
        myInfo["minimum_os_version"] = app_minimum_os_version
        myInfo["_metadata"]["creation_date"] = datetime.datetime.now()
        myInfo["uninstall_script"] = uninstall_script(appName,appVersion,appid)
        myInfo["preinstall_script"] = preinstall_script(appName,appVersion,appid)
        myInfo["installcheck_script"] = installcheck_script(appName,appVersion,appid)
        plistlib.writePlist(myInfo,vpp_apps_location+appName+".plist")
    print "ID: " + appid + "   Titel: " + appName.encode('ascii', 'ignore').decode('ascii')


sToken = readFile(tokenLoc)

vPPServiceConfigSrv = json.loads(requests.get('https://vpp.itunes.apple.com/WebObjects/MZFinance.woa/wa/VPPServiceConfigSrv').content)
try :
    context = (json.loads(json.loads(requests.get(vPPServiceConfigSrv["clientConfigSrvUrl"], data=json.dumps({"sToken": sToken})).content)["clientContext"])["hostname"])
except:
    print 'context neu holen'
    data = json.dumps({"sToken": sToken, "clientContext": "{\"hostname\": \"" + hostname + "\", \"guid\": \"" + str(uuid.uuid4()) + "\"}"})
    context = requests.get(vPPServiceConfigSrv["clientConfigSrvUrl"], data=data).content
    vPPServiceConfigSrv = json.loads(requests.get('https://vpp.itunes.apple.com/WebObjects/MZFinance.woa/wa/VPPServiceConfigSrv').content)

assets=json.loads(requests.get(vPPServiceConfigSrv["getVPPAssetsSrvUrl"], data=json.dumps({"sToken": sToken})).content)["assets"]
for asset in assets :
    appid = asset["adamIdStr"]
    updateEineApp(appid)

quit()

"""
{
    u'version': 2,
    u'meta': {
        u'language': {u'tag': u'de-de'},
        u'storefront': {u'cc': u'AT', u'id': u'143445'}
		},
    u'results': {
        u'409183694': {
            u'subtitle': u'Fantastische Pr\xe4sentationen',
            u'minimumOSVersion': u'10.13',
            u'editorialArtwork': {},
            u'releaseDate': u'2011-01-03',
            u'artistId': u'284417353',
            u'userRating': {u'ratingCountCurrentVersion': 14, u'valueCurrentVersion': 4, u'value': 4, u'ratingCount': 131},
            u'artistUrl': u'https://apps.apple.com/at/artist/apple/284417353?mt=12',
            u'isVppDeviceBasedLicensingEnabled': True,
            u'id': u'409183694',
            u'bundleId': u'com.apple.iWork.Keynote',
            u'genres': [
                {u'url': u'https://itunes.apple.com/at/genre/id12014', u'genreId': u'12014', u'name': u'Produktivit\xe4t', u'mediaType': u'12'},
                {u'url': u'https://itunes.apple.com/at/genre/id12001', u'genreId': u'12001', u'name': u'Wirtschaft', u'mediaType': u'12'}],
            u'copyright': u'\xa9 2003-2019 Apple Inc.',
            u'description': {u'standard': u'Mit Keynote und seinen benutzerfreundlichen, leistungsstarken Funktionen und vielen faszinierenden Effekten erstellst du schnell und einfach gro\xdfartige Pr\xe4sentationen.\n\nDie Themenauswahl enth\xe4lt 30 von Apple gestaltete neue und \xfcberarbeitete Themen. Wenn du ein passendes Thema f\xfcr deine Pr\xe4sentation gefunden hast, ersetze die Platzhalter f\xfcr Text und Grafiken einfach durch eigene Inhalte. Benutzerfreundliche Werkzeuge erm\xf6glichen es, Tabellen, Diagramme, Formen, Fotos und Videos zu Folien hinzuzuf\xfcgen und alles mit kinoreifen Animationen und \xdcberg\xe4ngen, die aussehen, als w\xe4ren sie von Profis f\xfcr Spezialeffekte erstellt worden, lebendig zu machen. Animiere deine Daten mit neuen, interaktiven S\xe4ulen-, Balken-, Streu- und Blasendiagrammen. Oder verwende Keynote Live, damit die Zuschauer deine Pr\xe4sentationen auf ihrem Mac, iPad, iPhone, iPod touch und \xfcber iCloud.com ansehen k\xf6nnen.\n\niCloud ist integriert, sodass die Pr\xe4sentationen auf deinen Ger\xe4ten immer auf dem neuesten Stand sind. Mit den Funktionen f\xfcr die Zusammenarbeit kann dein Team in Echtzeit auf einem Mac, iPad, iPhone oder iPod touch und \xfcber iWork f\xfcr iCloud sogar auf einem PC gemeinsam an einem Projekt arbeiten.\n\nMit Keynote bietet dir alle Werkzeuge, die du zum schnellen und einfachen Gestalten eindrucksvoller Pr\xe4sentationen brauchst.\n\nZusammenarbeit in Echtzeit\n\u2022 Dank dieser Funktion kann dein Team in Echtzeit gemeinsam und zeitgleich an einer Pr\xe4sentation arbeiten.\n\u2022 Diese Funktion ist direkt in Keynote auf dem Mac, iPad, iPhone und iPod touch integriert.\n\u2022 PC-Benutzer k\xf6nnen mit Keynote f\xfcr iCloud ebenfalls mitarbeiten.\n\u2022 Teile Dokumente mit allen oder nur mit bestimmten Personen.\n\u2022 Sieh jederzeit, wer zusammen mit dir an einer Pr\xe4sentation arbeitet.\n\u2022 Blende die Zeiger anderer Teilnehmer ein, um deren \xc4nderungen mitzuverfolgen.\n\u2022 Verf\xfcgbar f\xfcr Pr\xe4sentationen, die in iCloud oder Box gespeichert sind.\n\nSchneller Einstieg\n\u2022 W\xe4hle aus \xfcber 30 von Apple gestalteten Themen f\xfcr anspruchsvolle Pr\xe4sentationen aus.\n\u2022 Verwende die Folien\xfcbersicht zum Sichten der Pr\xe4sentation, Hinzuf\xfcgen oder Neuanordnen von Folien.\n\u2022 Gestalte mit interaktiven Diagrammen und Diagrammanimationen fesselnde Pr\xe4sentationen.\n\u2022 Zeige eine Live-Vorschau auf der Folienoberfl\xe4che beim Animieren von Folien an.\n\u2022 Verwende voreingestellte Stile f\xfcr sch\xf6n gestaltete Texte, Tabellen, Formen und Bilder.\n\u2022 Optimiere deine Pr\xe4sentationen mit einer Sammlung mit \xfcber 700 bearbeitbaren Formen.\n\u2022 \xd6ffne passwortgesch\xfctzte Pr\xe4sentationen schnell mit Touch ID auf unterst\xfctzten Macs.\n\nBenutzerfreundliche Grafikwerkzeuge\n\u2022 Arbeite pixelgenau mit Linealen und Hilfslinien.\n\u2022 Die vereinfachte Symbolleiste erm\xf6glicht den schnellen Zugriff auf Formen, Medien, Tabellen, Diagramme und Freigabeoptionen.\n\u2022 Verwende Donutdiagramme, um Daten auf ansprechende, neue Weise darzustellen.\n\u2022 Erg\xe4nze eine interaktive Bildergalerie, um eine Sammlung von Fotos anzuzeigen.\n\u2022 Entferne Bildhintergr\xfcnde mit \u201eTransparenz\u201c schnell und m\xfchelos.\n\u2022 Arbeite mit Freiformkurven, -formen und -masken.\n\u2022 F\xfcge Verbindungslinien hinzu.\n\nKinoreife Animationen\n\u2022 Gestalte Hollywood-reife Folien\xfcberg\xe4nge f\xfcr faszinierende Pr\xe4sentationen.\n\u2022 Verwende den Effekt \u201eZauberei\u201c zum Animieren und Umwandeln von Grafiken.\n\u2022 W\xe4hle gro\xdfartige Folien\xfcberg\xe4nge wie \u201eW\xe4scheleine\u201c, \u201eObjekt \u2013 W\xfcrfel\u201c, \u201eObjektspiegelung\u201c und \u201eObjekt \u2013 Auf-/Abtauchen\u201c aus.\n\u2022 Verwende Text- und Objektanimationen wie \u201eVerschwinden\u201c, \u201eZerbr\xf6ckeln\u201c sowie \u201e\xdcberblenden und Skalieren\u201c.\n\u2022 Integriere Konturanimationen, die f\xfcr einen bleibenden Eindruck mit nur einem Klick sorgen.\n\nPr\xe4sentation vorf\xfchren\n\u2022 Anpassbarer Moderatormonitor mit Unterst\xfctzung f\xfcr bis zu sechs Displays\n\u2022 Aufgezeichnete Sprechertexte\n\nEinige Funktionen erfordern u. U. Internetzugang. Hierf\xfcr k\xf6nnen Geb\xfchren anfallen. Es gelten zus\xe4tzliche Bedingungen.'},
            u'softwareInfo': {u'privacyPolicyUrl': u'https://www.apple.com/legal/privacy/de-ww', u'supportUrl': u'http://www.apple.com/de/support/keynote/', u'languagesDisplayString': u'Deutsch, Arabisch, Chinesisch (Hongkong), D\xe4nisch, Englisch, Finnisch, Franz\xf6sisch, Griechisch, Hebr\xe4isch, Hindi, Indonesisch, Italienisch, Japanisch, Katalanisch, Koreanisch, Kroatisch, Malaiisch, Niederl\xe4ndisch, Norwegisch, Polnisch, Portugiesisch, Rum\xe4nisch, Russisch, Schwedisch, Slowakisch, Spanisch, Thai, Tradit. Chinesisch, Tschechisch, T\xfcrkisch, Ukrainisch, Ungarisch, Vereinf. Chinesisch, Vietnamesisch', u'seller': u'Apple Distribution International', u'websiteUrl': u'http://www.apple.com/de/keynote/', u'privacyPolicyTextUrl': None, u'requirementsString': u'macOS 10.13 oder neuer', u'eulaUrl': u'https://itunes.apple.com/WebObjects/MZStore.woa/wa/viewEula?cc=at&id=409183694'},
            u'shortUrl': u'https://apps.apple.com/at/app/keynote/id409183694?mt=12',
            u'offers': [{
                u'actionText': {u'downloaded': u'Installiert', u'medium': u'Laden', u'short': u'Laden', u'downloading': u'Wird installiert', u'long': u'Laden'},
                u'assets': [{u'flavor': u'macSoftware', u'size': 461332733}],
            	u'priceFormatted': u'0,00\xa0\u20ac',
            	u'price': 0,
            	u'version': {u'externalId': 831242334, u'display': u'9.1'},
            	u'buyParams': u'productType=C&price=0&salableAdamId=409183694&pricingParameters=STDQ&pg=default&marketType=ENT&appExtVrsId=831242334',
            	u'type': u'get'}],
        	u'nameSortValue': u'Keynote',
        	u'deviceFamilies': [u'mac'],
        	u'contentRatingsBySystem': {u'appsApple': {u'rank': 1, u'name': u'4+', u'value': 100}},
        	u'artwork': {u'textColor4': u'007ec2', u'supportsLayeredImage': False, u'bgColor': u'000000', u'url': u'https://is4-ssl.mzstatic.com/image/thumb/Purple113/v4/24/d8/69/24d869b4-a24d-d8cf-0e83-3941ea6fbc48/AppIcon-0-85-220-0-0-0-0-4-0-0-0-2x-sRGB-0-0-0.png/{w}x{h}bb.{f}', u'hasAlpha': True, u'textColor1': u'fdfdfd', u'textColor2': u'009df3', u'textColor3': u'cacaca', u'width': 1024, u'height': 1024, u'hasP3': False},
        	u'latestVersionReleaseDate': u'25.06.2019',
        	u'kind': u'desktopApp',
        	u'name': u'Keynote',
        	u'nameRaw': u'Keynote',
        	u'url': u'https://apps.apple.com/at/app/keynote/id409183694?mt=12',
        	u'genreNames': [u'Produktivit\xe4t', u'Wirtschaft'],
			u'artistName': u'Apple',
        	u'whatsNew': u'\u2022Bearbeite Folienvorlagen w\xe4hrend der Zusammenarbeit an einer Pr\xe4sentation.\n\u2022Formatiere Text durch F\xfcllen mit Verl\xe4ufen oder Bildern oder durch Anwenden der neuen Konturstile.\n\u2022Binde Bilder, Formen und Gleichungen in Textfelder ein, sodass sie zusammen mit dem Text bewegt werden.\n\u2022Platziere mithilfe der Gesichtserkennung auf intelligente Weise Motive in Fotos in Platzhaltern und Objekten.'
		}
	},
	u'isAuthenticated': False
}
"""
