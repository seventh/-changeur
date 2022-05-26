#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tentative de copie du jeu «Freeways»
"""

# Dépendance(s) standard(s)
import logging
import math
import random

# Dépendance(s) interne(s)
import format_1

# Dépendance(s) externe(s)
import pygame


class V2:
    """Vecteur à deux dimensions
    """
    def __init__(self, largeur, hauteur):
        self.largeur = largeur
        self.hauteur = hauteur

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


class Item(dict):
    def __init__(self, graphe, *, est_arête, **attributs):
        super().__init__(attributs)

        self.graphe = graphe
        self.est_arête = est_arête
        self.liaisons = list()

    def __eq__(self, autre):
        return id(self) == id(autre)

    def __repr__(self):
        return f"{self.__class__.__name__}(0x{id(self):x})(est_arête={self.est_arête})"

    # def __del__(self):
    #     self.détacher(*self.liaisons)
    #     if self.est_arête:
    #         self.graphe.liens.remove(self)
    #     else:
    #         self.graphe.nœuds.remove(self)
    #     self.graphe = None

    def associer(self, *autres):
        for a in autres:
            self.liaisons.append(a)
            a.liaisons.append(self)

    def détacher(self, *autres):
        for a in autres:
            a.liaisons.remove(self)
            self.liaisons.remove(a)

    def est_similaire(self, autre):
        retour = (self.est_arête == autre.est_arête
                  and len(self.liaisons) == len(autre.liaisons))

        i = 0
        while retour and i < len(self.liaisons):
            try:
                autre.liaisons.index(self.liaisons[i])
                i += 1
            except ValueError:
                retour = False

        return retour


class Graphe:
    def __init__(self):
        # Sommets
        self.nœuds = list()
        # Arêtes
        self.liens = list()

    def __repr__(self):
        lignes = list()
        for i, n in enumerate(self.nœuds):
            assert (not n.est_arête)
            liens = list()
            for l in n.liaisons:
                assert (l.est_arête)
                j = self.liens.index(l)
                liens.append(f"L{j}")
            liens.sort()
            lignes.append(f"Nœud N{i} → {', '.join(liens)}")

        for i, l in enumerate(self.liens):
            assert (l.est_arête)
            nœuds = list()
            for n in l.liaisons:
                assert (not n.est_arête)
                j = self.nœuds.index(n)
                nœuds.append(f"N{j}")
            nœuds.sort()
            lignes.append(f"Lien L{i} → {', '.join(nœuds)}")

        return "\n".join(lignes)

    def ajouter_nœud(self):
        retour = Item(self, est_arête=False)
        self.nœuds.append(retour)
        return retour

    def ajouter_lien(self):
        retour = Item(self, est_arête=True)
        self.liens.append(retour)
        return retour

    def fusionner_nœuds(self, nid, but):
        # Remplacement de 'nid' par 'but' dans tous ses liens
        for l in list(nid.liaisons):
            if but not in l.liaisons:
                l.associer(but)
            l.détacher(nid)
            if len(l.liaisons) < 2:
                self.supprimer_lien(l)

        # Suppression de l'ancien nœud
        assert (len(nid.liaisons) == 0)
        self.supprimer_nœud(nid)

        # Suppression des relations identiques
        recommencer = True
        while recommencer:
            recommencer = False
            for i, l in enumerate(but.liaisons):
                for k in but.liaisons[i + 1:]:
                    if l.est_similaire(k):
                        recommencer = True
                        g.supprimer_lien(k)
                        break
                if recommencer:
                    break

    def iter_nœuds(self):
        yield from self.nœuds

    def iter_liens(self):
        yield from self.liens

    def supprimer_nœud(self, nœud):
        """La suppression d'un nœud provoque la suppression de tous les liens
        orphelins
        """
        liaisons = list(nœud.liaisons)
        for l in liaisons:
            g.supprimer_lien(l)
        assert (len(nœud.liaisons) == 0)
        self.nœuds.remove(nœud)
        nœud.graphe = None

    def supprimer_lien(self, lien):
        lien.détacher(*lien.liaisons)
        self.liens.remove(lien)
        lien.graphe = None


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


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    random.seed(1977)
    pygame.init()

    rayon = 10

    noir = (0, 0, 0)
    # rouge = (255, 0, 0)
    # vert = (0, 255, 0)
    # bleu = (0, 0, 255)
    # jaune = (0, 255, 255)

    dimensions = V2(640, 480)
    écran = pygame.display.set_mode(dimensions.en_tuple())

    # Chargement du niveau
    val = format_1.Validateur(".")
    niveau = format_1.charger("niveau-0.0.json", "échangeur", val)
    g = Graphe()
    for r in niveau["routes"]:
        couleur = couleur_aléatoire(0)
        if "entrée" in r:
            entrée = g.ajouter_nœud()
            entrée["amovible"] = False
            entrée["couleur"] = couleur
            entrée["position"] = V2(r["entrée"]["largeur"],
                                    r["entrée"]["hauteur"])
            entrée["palier"] = 0

        if "sortie" in r:
            sortie = g.ajouter_nœud()
            sortie["amovible"] = False
            sortie["couleur"] = couleur
            sortie["position"] = V2(r["sortie"]["largeur"],
                                    r["sortie"]["hauteur"])
            sortie["palier"] = 0

    # Boucle d'interaction
    point = None  # Nœud sélectionné
    modif = True
    while True:
        if modif:
            écran.fill(noir)

            for l in sorted(g.iter_liens(), key=lambda l: l["palier"]):
                pygame.draw.line(écran, l["couleur"],
                                 l.liaisons[0]["position"].en_tuple(),
                                 l.liaisons[1]["position"].en_tuple(), rayon)
            for n in g.iter_nœuds():
                pygame.draw.circle(écran, n["couleur"],
                                   n["position"].en_tuple(), rayon)

            pygame.display.flip()

            modif = False

        évt = pygame.event.wait()
        # print(évt)
        if (évt.type == pygame.KEYDOWN and évt.key == pygame.K_ESCAPE):
            break

        modif = False
        if évt.type == pygame.MOUSEBUTTONUP:
            if point is not None:
                nœud, dn = nœud_proche(g, point["position"], point)
                if dn <= rayon:
                    logging.info("Fusion de deux nœuds")
                    logging.debug("*** Avant")
                    logging.debug(g)
                    if nœud["amovible"]:
                        g.fusionner_nœuds(nœud, point)
                    else:
                        g.fusionner_nœuds(point, nœud)
                    logging.debug("*** Après")
                    logging.debug(g)
                    modif = True

                point = None

        elif évt.type == pygame.MOUSEBUTTONDOWN:
            logging.debug("*** Avant")
            logging.debug(g)
            position = V2.de_tuple(évt.pos)
            nœud, dn = nœud_proche(g, position)
            lien, dl = lien_proche(g, position)
            if dn <= rayon:
                if nœud["amovible"]:
                    logging.info("Sélection d'un nœud")
                    if évt.button == 1:
                        # Bouton gauche : sélection du nœud
                        point = nœud
                    elif évt.button == 3:
                        # Bouton droit : suppression du nœud
                        g.supprimer_nœud(nœud)
                        logging.debug("*** Après")
                        logging.debug(g)
                        modif = True

            elif dl <= rayon / 2:
                logging.info("Sélection d'un lien")
                if évt.button == 1:
                    # Bouton gauche : césure du segment
                    point = g.ajouter_nœud()
                    point["position"] = position
                    point["couleur"] = lien["couleur"]
                    point["amovible"] = True
                    point["palier"] = lien["palier"]
                    lg = g.ajouter_lien()
                    lg["couleur"] = lien["couleur"]
                    lg["palier"] = lien["palier"]
                    lg.associer(point, lien.liaisons[0])
                    ld = g.ajouter_lien()
                    ld["couleur"] = lien["couleur"]
                    ld["palier"] = lien["palier"]
                    ld.associer(point, lien.liaisons[1])
                    g.supprimer_lien(lien)
                    logging.debug("*** Après")
                    logging.debug(g)
                    modif = True
                elif évt.button == 3:
                    # Bouton droit: suppression du lien
                    g.supprimer_lien(lien)
                    modif = True
                elif évt.button == 4:
                    # Molette haut → augmentation du palier
                    if lien["palier"] + 1 < PALIERS:
                        lien["palier"] += 1
                        if not carte_est_valide(g):
                            lien["palier"] -= 1
                        else:
                            lien["couleur"] = augmenter_intensité(
                                lien["couleur"])
                            modif = True
                elif évt.button == 5:
                    # Molette bas → diminution du palier
                    if lien["palier"] > 0:
                        lien["palier"] -= 1
                        if not carte_est_valide(g):
                            lien["palier"] += 1
                        else:
                            lien["couleur"] = diminuer_intensité(
                                lien["couleur"])
                            modif = True

            else:
                logging.info("Ajout d'un nœud/lien")
                # On ajoute un nouveau nœud…
                point = g.ajouter_nœud()
                point["position"] = position
                point["couleur"] = couleur_aléatoire(0)
                point["amovible"] = True
                point["palier"] = 0
                # …et éventuellement un nouveau lien
                logging.debug(g)
                if dn <= 10 * rayon:
                    point["couleur"] = nœud["couleur"]
                    point["palier"] = nœud["palier"]
                    lien = g.ajouter_lien()
                    lien["couleur"] = nœud["couleur"]
                    lien["palier"] = nœud["palier"]
                    lien.associer(nœud, point)
                logging.debug("*** Après")
                logging.debug(g)
                modif = True

            nœud = None
            lien = None

        elif évt.type == pygame.MOUSEMOTION:
            if point is not None:
                position = V2.de_tuple(évt.pos)
                ancienne = point["position"]
                point["position"] = position
                if carte_est_valide(g):
                    modif = True
                else:
                    point["position"] = ancienne
                    # La sélection du nœud est perdue : reprise de l'action
                    # 'pygame.MOUSEBUTTONUP'
                    nœud, dn = nœud_proche(g, point["position"], point)
                    if dn <= rayon:
                        logging.info("Fusion de deux nœuds")
                        logging.debug("*** Avant")
                        logging.debug(g)
                        if nœud["amovible"]:
                            g.fusionner_nœuds(nœud, point)
                        else:
                            g.fusionner_nœuds(point, nœud)
                        logging.debug("*** Après")
                        logging.debug(g)
                        modif = True

                    point = None
