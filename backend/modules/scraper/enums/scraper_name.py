from django.db import models


class ScraperName(models.TextChoices):
    LINKEDIN = 'linkedin', 'LinkedIn'
    MICROSOFT = 'Microsoft', 'Microsoft'
    NATWEST = 'NatWest Group', 'NatWest Group'
    ADOBE = 'Adobe', 'Adobe'
    ORACLE = 'Oracle', 'Oracle'
    AIRBUS = 'Airbus', 'Airbus'
    MASTERCARD = 'Mastercard', 'Mastercard'
    JPMORGANCHASE = 'JPMorganChase', 'JPMorganChase'
    NETAPP = 'NetApp', 'NetApp'
    CISCO = 'Cisco', 'Cisco'
    WELLFOUND = 'Wellfound', 'Wellfound'
    GOLDMAN_SACHS = 'Goldman Sachs', 'Goldman Sachs'
    BARCLAYS = 'Barclays', 'Barclays'
