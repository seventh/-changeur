# -*- coding: utf-8 -*-

# Dépendance(s) standard(s)
import json
import logging
import os

# Dépendance(s) interne(s)

# Dépendance(s) externe(s)
import jsonschema


class Validateur:
    """Validation JSON schema
    """

    def __init__(self, chemin):
        """Charge tous les schémas disponibles au chemin correspondant
        """
        self.schémas = dict()
        chemin, répertoires, fichiers = next(os.walk(chemin))
        for f in fichiers:
            if f.endswith(".schema.json"):
                with open(os.path.join(chemin, f), "rt") as flux:
                    schéma = json.loads(flux.read())
                    self.schémas[f[:-12]] = schéma

    def valider(self, nom_schéma, sous_réf, contenu):
        retour = True
        try:
            schéma = self.schémas[nom_schéma]
            if sous_réf is not None:
                schéma = schéma["$defs"][sous_réf]
            jsonschema.validate(contenu, schéma)
        except jsonschema.exceptions.ValidationError as e:
            logging.warning(f"Non-respect du format «{nom_schéma}»")
            logging.warning(e)
            retour = False
        except jsonschema.exceptions.SchemaError as e:
            logging.error(f"Le schéma «{nom_schéma}» est tout pourri")
            logging.error(e)
            retour = False
        return retour


def charger(nom_fichier, nom_schéma, validateur):
    contenu = dict()
    with open(nom_fichier, "rt") as entrée:
        données = entrée.read()
        contenu = json.loads(données)
    # if not validateur.valider(nom_schéma, "niveau", contenu):
    #    logging.warning(f"Pas moyen de valider '{nom_fichier}'")
    return contenu
