# -*- coding: utf-8 -*-
"""Modélisation d'un graphe quelconque
"""


class Item(dict):
    """Élément du graphe, utilisé indifféremment pour les arêtes comme pour
    les sommets.

    À FAIRE : le fait que cette classe hérite de «dict» est une mauvaise idée.
    L'origine de cet héritage était par fainéantise et ne pas vouloir définir
    les méthodes «(get/set/del)item», mais a conduit à redéfinir «eq» et
    certainement d'autres, comme «hash». De même qu'un Item conserve un lien
    vers son graphe parent, il doit prévoir un unique attribut «étiquette» ou
    quelque chose du genre.
    """
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
                        self.supprimer_lien(k)
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
            self.supprimer_lien(l)
        assert (len(nœud.liaisons) == 0)
        self.nœuds.remove(nœud)
        nœud.graphe = None

    def supprimer_lien(self, lien):
        lien.détacher(*lien.liaisons)
        self.liens.remove(lien)
        lien.graphe = None
