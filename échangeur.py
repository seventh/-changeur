#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tentative de copie du jeu «Freeways»
"""

# Dépendance(s) standard(s)
import dataclasses
import enum
import logging
import math
import random

# Dépendance(s) interne(s)
import format_1
import graphe

# Dépendance(s) externe(s)
import pygame


class V2:
    """Vecteur à deux dimensions
    """
    def __init__(self, largeur, hauteur):
        self.largeur = largeur
        self.hauteur = hauteur

    def __repr__(self):
        return f"{self.__class__.__name__}(0x{id(self):x}(largeur={self.largeur}, hauteur={self.hauteur})"

    def __str__(self):
        return f"({self.largeur}, {self.hauteur})"

    def __neg__(self):
        return V2(-self.largeur, -self.hauteur)

    def __sub__(self, autre):
        return V2(self.largeur - autre.largeur, self.hauteur - autre.hauteur)

    @staticmethod
    def de_tuple(paire):
        return V2(paire[0], paire[1])

    def en_tuple(self):
        return (self.largeur, self.hauteur)

    def norme(self):
        return math.sqrt(self.norme2())

    def norme2(self):
        return self.scalaire(self)

    def scalaire(self, autre):
        return self.largeur * autre.largeur + self.hauteur * autre.hauteur

    def vectoriel(self, autre):
        return self.largeur * autre.hauteur - self.hauteur * autre.largeur


class Biome(enum.IntEnum):

    AUCUN = enum.auto()
    ENTRÉE = enum.auto()
    SORTIE = enum.auto()
    FORÊT = enum.auto()
    USINE = enum.auto()
    FLEUVE = enum.auto()


@dataclasses.dataclass
class Obstacle:

    coin_min: V2
    coin_max: V2
    biome: Biome

    def intersection(self, nid, but):
        retour = False
        v = but - nid
        vl = V2(self.coin_max.largeur - self.coin_min.largeur, 0)
        vh = V2(0, self.coin_max.hauteur - self.coin_min.hauteur)

        if (intersection(nid, v, self.coin_min, vl)
                or intersection(nid, v, self.coin_min, vh)
                or intersection(nid, v, self.coin_max, -vl)
                or intersection(nid, v, self.coin_max, -vh)):
            retour = True

        return retour


@dataclasses.dataclass
class Liaison:

    nid: object
    but: object
    débit: int


PALIERS = 3


def couleur_aléatoire(palier):
    """Couleur d'intensité aléatoire, selon le palier choisi
    """
    composante_min = round(255 * palier / PALIERS)
    composante_max = round(255 * (palier + 1) / PALIERS)
    composantes = list()
    for k in range(3):
        composantes.append(random.randint(composante_min, composante_max))
    return tuple(composantes)


def augmenter_intensité(couleur):
    composantes = list()
    for c in couleur:
        d = min(c + 255 / PALIERS, 255)
        composantes.append(d)
    return tuple(composantes)


def diminuer_intensité(couleur):
    composantes = list()
    for c in couleur:
        d = max(c - 255 / PALIERS, 0)
        composantes.append(d)
    return tuple(composantes)


def nœuds_communs(lien_a, lien_b):
    retour = list()
    for l in lien_a.liaisons:
        if l in lien_b.liaisons:
            retour.append(l)
    return retour


def nœud_proche(graphe, position, *exclus):
    retour = None
    distance = float('inf')
    for nœud in graphe.iter_nœuds():
        if nœud not in exclus:
            d2 = (nœud["position"] - position).norme2()
            if d2 < distance:
                retour = nœud
                distance = d2
    distance = math.sqrt(distance)

    return retour, distance


def lien_proche(graphe, position):
    retour = None
    distance = float('inf')
    for lien in graphe.iter_liens():
        nb = lien.liaisons[1]["position"] - lien.liaisons[0]["position"]
        np = position - lien.liaisons[0]["position"]
        h = abs(nb.vectoriel(np) / nb.norme())
        if (0 <= nb.scalaire(np) <= nb.norme2() and h < distance):
            retour = lien
            distance = h

    return retour, distance


def carte_est_valide(graphe):
    """Un graphe est valide si aucun lien ne croise un autre lien de même
    'palier'
    """
    retour = True
    for i, lien in enumerate(graphe.iter_liens()):
        # On considère que tous les liens sont des liens binaires,
        # c'est-à-dire que chaque lien implique 2 nœuds différents, ni
        # plus, ni moins
        nid1 = lien.liaisons[0]["position"]
        v1 = lien.liaisons[1]["position"] - lien.liaisons[0]["position"]
        for autre in graphe.liens[i + 1:]:
            # On ne regarde que les liens qui n'ont pas de nœud en commun
            if (lien["palier"] == autre["palier"]
                    and len(nœuds_communs(lien, autre)) == 0):
                nid2 = autre.liaisons[0]["position"]
                v2 = autre.liaisons[1]["position"] - \
                    autre.liaisons[0]["position"]
                # Équation à vérifier (en deux dimensions) :
                # v1 * t1 - v2 * t2 = nid2 - nid1
                # avec t1 ∈ [0, 1] et t2 ∈ [0, 1]
                dét = v1.hauteur * v2.largeur - v1.largeur * v2.hauteur
                if dét != 0:
                    écart = nid2 - nid1
                    t1 = (v2.largeur * écart.hauteur -
                          v2.hauteur * écart.largeur) / dét
                    t2 = (v1.largeur * écart.hauteur -
                          v1.hauteur * écart.largeur) / dét
                    logging.debug(f"{t1} et {t2}")
                    if 0 <= t1 <= 1 and 0 <= t2 <= 1:
                        retour = False
                        break
            if not retour:
                break

    return retour


def intersection(nid1, v1, nid2, v2):
    """Y a-t-il une intersection entre les deux segments ?
    """
    retour = False
    écart = nid2 - nid1
    # Équation à vérifier (en deux dimensions) :
    # v1 * t1 - v2 * t2 = nid2 - nid1
    # avec t1 ∈ [0, 1] et t2 ∈ [0, 1]
    dét = v1.hauteur * v2.largeur - v1.largeur * v2.hauteur
    if dét != 0:
        t1 = (v2.largeur * écart.hauteur - v2.hauteur * écart.largeur) / dét
        t2 = (v1.largeur * écart.hauteur - v1.hauteur * écart.largeur) / dét
        logging.debug(f"{t1} et {t2}")
        if 0 <= t1 <= 1 and 0 <= t2 <= 1:
            retour = True
    else:
        # Soit les points sont colinéaires, soit les segments sont parallèles
        # Équation à vérifier :
        # v1 * t = nid2 - nid1
        cos = abs(v1.scalaire(écart)) / math.sqrt(v1.norme2() * écart.norme2())
        if cos - 1 >= -1e-7:
            logging.debug("Aïe !")
            retour = True

    return retour


class Niveau:
    def __init__(self):
        self.graphe = graphe.Graphe()
        self.obstacles = list()
        self.flux = list()

    def charger(self, nom_fichier):
        val = format_1.Validateur(".")
        données = format_1.charger(nom_fichier, "échangeur", val)
        points = dict()
        for r in données["routes"]:
            couleur = couleur_aléatoire(0)
            if "entrée" in r:
                entrée = self.graphe.ajouter_nœud()
                entrée["amovible"] = False
                entrée["biome"] = Biome.ENTRÉE
                entrée["couleur"] = couleur
                entrée["position"] = V2(r["entrée"]["largeur"],
                                        r["entrée"]["hauteur"])
                entrée["palier"] = 0
                points[f"but/{r['nom']}"] = entrée

            if "sortie" in r:
                sortie = self.graphe.ajouter_nœud()
                sortie["amovible"] = False
                sortie["biome"] = Biome.SORTIE
                sortie["couleur"] = couleur
                sortie["position"] = V2(r["sortie"]["largeur"],
                                        r["sortie"]["hauteur"])
                sortie["palier"] = 0
                points[f"nid/{r['nom']}"] = sortie

        # Obstacles
        if "obstacles" in données:
            for o in données["obstacles"]:
                coin_min = V2(o["position"]["inf"]["largeur"],
                              o["position"]["inf"]["hauteur"])
                coin_max = V2(o["position"]["sup"]["largeur"],
                              o["position"]["sup"]["hauteur"])
                biome = Biome[o["rôle"]]
                obstacle = Obstacle(coin_min, coin_max, biome)
                self.obstacles.append(obstacle)

        # Objectifs de connexion
        for l in données["liaisons"]:
            clef = f"nid/{l['nid']}"
            nid = points[clef]
            clef = f"but/{l['but']}"
            but = points[clef]
            self.flux.append(Liaison(nid, but, l["flux"]))

    def est_dans_un_obstacle(self, position):
        """Vrai ssi la position est occupée par un des obstacles du niveau
        """
        logging.debug(position)
        retour = False
        for o in self.obstacles:
            if (o.coin_min.largeur <= position.largeur <= o.coin_max.largeur
                    and o.coin_min.hauteur <= position.hauteur <=
                    o.coin_max.hauteur):
                retour = True
                break
        return retour

    def valider_mouvement(self, sommet, position):
        """Le mouvement du sommet à la position donnée est autorisé si:

        - il ne se retrouve pas en collision avec un obstacle
        - aucun des tronçons auquel il est lié n'entre en collision avec un
        obstacle
        - aucun des tronçons auquel il est lié n'intersecte un tronçon de même
        palier
        """
        retour = True
        if self.est_dans_un_obstacle(position):
            retour = False
        else:
            ancienne = sommet["position"]
            sommet["position"] = position
            for lien in sommet.liaisons:
                nid1 = lien.liaisons[0]["position"]
                v1 = lien.liaisons[1]["position"] - lien.liaisons[0]["position"]
                # ÀDU : On vérifie la collision avec un obstacle
                for o in self.obstacles:
                    if o.intersection(lien.liaisons[0]["position"],
                                      lien.liaisons[1]["position"]):
                        logging.debug(f"Intersection avec {o} !")
                        retour = False
                        break
                if not retour:
                    break

                # On vérifie l'intersection avec un autre lien de même palier
                for autre in self.graphe.liens:
                    # On ne regarde que les liens qui n'ont pas de nœud commun
                    if (lien["palier"] == autre["palier"]
                            and len(nœuds_communs(lien, autre)) == 0):
                        nid2 = autre.liaisons[0]["position"]
                        v2 = autre.liaisons[1]["position"] - \
                            autre.liaisons[0]["position"]
                        if intersection(nid1, v1, nid2, v2):
                            retour = False
                            break
                if not retour:
                    break
            sommet["position"] = ancienne

        return retour

    def est_complet(self):
        """Vrai ssi toutes les liaisons objectives sont effectives
        """
        retour = True
        for l in self.flux:
            if not self.sont_connectés(l.nid, l.but):
                retour = False
                break
        return retour

    def sont_connectés(self, nid, but):
        """Vrai ssi un chemin existe entre les deux sommets
        """
        trouvé = False
        atteints = [nid]
        nouveaux = [nid]
        while not (trouvé or len(nouveaux) == 0):
            muchmuch = list()
            for s in nouveaux:
                for l in s.liaisons:
                    for autre in l.liaisons:
                        if autre is but:
                            trouvé = True
                            break
                        elif autre not in atteints:
                            muchmuch.append(autre)
                            atteints.append(autre)
                    if trouvé:
                        break
                if trouvé:
                    break
            nouveaux = muchmuch
        return trouvé


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    random.seed(1977)
    pygame.init()

    rayon = 10

    noir = (0, 0, 0)
    # rouge = (255, 0, 0)
    vert = (0, 255, 0)
    # bleu = (0, 0, 255)
    # jaune = (0, 255, 255)

    dimensions = V2(640, 480)
    écran = pygame.display.set_mode(dimensions.en_tuple())

    # Chargement du niveau
    NIVEAU = Niveau()
    NIVEAU.charger("niveau-1.0.json")

    # Boucle d'interaction
    point = None  # Nœud sélectionné
    modif = True
    while True:
        if modif:
            écran.fill(noir)

            # Liaisons
            for l in sorted(NIVEAU.graphe.iter_liens(),
                            key=lambda l: l["palier"]):
                pygame.draw.line(écran, l["couleur"],
                                 l.liaisons[0]["position"].en_tuple(),
                                 l.liaisons[1]["position"].en_tuple(), rayon)
            # Sommets
            for n in NIVEAU.graphe.iter_nœuds():
                pygame.draw.circle(écran, n["couleur"],
                                   n["position"].en_tuple(), rayon)
            # Obstacles
            for o in NIVEAU.obstacles:
                pygame.draw.rect(écran, vert,
                                 (o.coin_min.en_tuple(),
                                  (o.coin_max - o.coin_min).en_tuple()))

            pygame.display.flip()

            modif = False

        if NIVEAU.est_complet():
            logging.info("Bravo !")

        évt = pygame.event.wait()
        # print(évt)
        if (évt.type == pygame.KEYDOWN and évt.key == pygame.K_ESCAPE):
            break

        modif = False
        if évt.type == pygame.MOUSEBUTTONUP:
            if point is not None:
                nœud, dn = nœud_proche(NIVEAU.graphe, point["position"], point)
                if dn <= rayon:
                    logging.info("Fusion de deux nœuds")
                    logging.debug("*** Avant")
                    logging.debug(NIVEAU.graphe)
                    if nœud["amovible"]:
                        NIVEAU.graphe.fusionner_nœuds(nœud, point)
                    else:
                        NIVEAU.graphe.fusionner_nœuds(point, nœud)
                    logging.debug("*** Après")
                    logging.debug(NIVEAU.graphe)
                    modif = True

                point = None

        elif évt.type == pygame.MOUSEBUTTONDOWN:
            logging.debug("*** Avant")
            logging.debug(NIVEAU.graphe)
            position = V2.de_tuple(évt.pos)
            nœud, dn = nœud_proche(NIVEAU.graphe, position)
            lien, dl = lien_proche(NIVEAU.graphe, position)
            if dn <= rayon:
                if nœud["amovible"]:
                    logging.info("Sélection d'un nœud")
                    if évt.button == 1:
                        # Bouton gauche : sélection du nœud
                        point = nœud
                    elif évt.button == 3:
                        # Bouton droit : suppression du nœud
                        NIVEAU.graphe.supprimer_nœud(nœud)
                        logging.debug("*** Après")
                        logging.debug(NIVEAU.graphe)
                        modif = True

            elif dl <= rayon / 2:
                logging.info("Sélection d'un lien")
                if évt.button == 1:
                    # Bouton gauche : césure du segment
                    point = NIVEAU.graphe.ajouter_nœud()
                    point["position"] = position
                    point["couleur"] = lien["couleur"]
                    point["amovible"] = True
                    point["biome"] = Biome.AUCUN
                    point["palier"] = lien["palier"]
                    lg = NIVEAU.graphe.ajouter_lien()
                    lg["couleur"] = lien["couleur"]
                    lg["palier"] = lien["palier"]
                    lg.associer(point, lien.liaisons[0])
                    ld = NIVEAU.graphe.ajouter_lien()
                    ld["couleur"] = lien["couleur"]
                    ld["palier"] = lien["palier"]
                    ld.associer(point, lien.liaisons[1])
                    NIVEAU.graphe.supprimer_lien(lien)
                    logging.debug("*** Après")
                    logging.debug(NIVEAU.graphe)
                    modif = True
                elif évt.button == 3:
                    # Bouton droit: suppression du lien
                    NIVEAU.graphe.supprimer_lien(lien)
                    modif = True
                elif évt.button == 4:
                    # Molette haut → augmentation du palier
                    if lien["palier"] + 1 < PALIERS:
                        lien["palier"] += 1
                        if not carte_est_valide(NIVEAU.graphe):
                            lien["palier"] -= 1
                        else:
                            lien["couleur"] = augmenter_intensité(
                                lien["couleur"])
                            modif = True
                elif évt.button == 5:
                    # Molette bas → diminution du palier
                    if lien["palier"] > 0:
                        lien["palier"] -= 1
                        if not carte_est_valide(NIVEAU.graphe):
                            lien["palier"] += 1
                        else:
                            lien["couleur"] = diminuer_intensité(
                                lien["couleur"])
                            modif = True

            else:
                if NIVEAU.est_dans_un_obstacle(position):
                    logging.debug("Intersection avec un obstacle")
                else:
                    logging.info("Ajout d'un nœud/lien")
                    # On ajoute un nouveau nœud…
                    point = NIVEAU.graphe.ajouter_nœud()
                    point["position"] = position
                    point["couleur"] = couleur_aléatoire(0)
                    point["amovible"] = True
                    point["biome"] = Biome.AUCUN
                    point["palier"] = 0
                    # …et éventuellement un nouveau lien
                    logging.debug(NIVEAU.graphe)
                    if dn <= 10 * rayon:
                        point["couleur"] = nœud["couleur"]
                        point["palier"] = nœud["palier"]
                        lien = NIVEAU.graphe.ajouter_lien()
                        lien["couleur"] = nœud["couleur"]
                        lien["palier"] = nœud["palier"]
                        lien.associer(nœud, point)
                    logging.debug("*** Après")
                    logging.debug(NIVEAU.graphe)
                    modif = True

            nœud = None
            lien = None

        elif évt.type == pygame.MOUSEMOTION:
            if point is not None:
                position = V2.de_tuple(évt.pos)
                if NIVEAU.valider_mouvement(point, position):
                    point["position"] = position
                    modif = True
                else:
                    # La sélection du nœud est perdue : reprise de l'action
                    # 'pygame.MOUSEBUTTONUP'
                    nœud, dn = nœud_proche(NIVEAU.graphe, point["position"],
                                           point)
                    if dn <= rayon:
                        logging.info("Fusion de deux nœuds")
                        logging.debug("*** Avant")
                        logging.debug(NIVEAU.graphe)
                        if nœud["amovible"]:
                            NIVEAU.graphe.fusionner_nœuds(nœud, point)
                        else:
                            NIVEAU.graphe.fusionner_nœuds(point, nœud)
                        logging.debug("*** Après")
                        logging.debug(NIVEAU.graphe)
                        modif = True

                    point = None
