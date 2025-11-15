import pygame

pygame.init()

# Création de la fenêtre
LARGEUR, HAUTEUR = 800, 600
ecran = pygame.display.set_mode((LARGEUR, HAUTEUR))
pygame.display.set_caption("Zone de jeu 2/3 – 1/3")

# Chargement du fond
fond = pygame.image.load("fond.jpg")
fond = pygame.transform.scale(fond, (LARGEUR, HAUTEUR))

# Position initiale du carré
x, y = 100, 100
vitesse = 2
TAILLE_CARRE = 50

# Définir la limite de zone : 2/3 de la largeur totale
ZONE_JEU_LARGEUR = (2 * LARGEUR) // 3  # → environ 533 px sur 800

continuer = True
while continuer:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            continuer = False

    # Gestion des touches
    touches = pygame.key.get_pressed()
    if touches[pygame.K_UP]:
        y -= vitesse
    if touches[pygame.K_DOWN]:
        y += vitesse
    if touches[pygame.K_LEFT]:
        x -= vitesse
    if touches[pygame.K_RIGHT]:
        x += vitesse

    # Limiter les déplacements à la zone gauche
    if x < 0:
        x = 0
    if y < 0:
        y = 0
    if x > ZONE_JEU_LARGEUR - TAILLE_CARRE:
        x = ZONE_JEU_LARGEUR - TAILLE_CARRE
    if y > HAUTEUR - TAILLE_CARRE:
        y = HAUTEUR - TAILLE_CARRE

    # Dessin
    ecran.blit(fond, (0, 0))

    # Ligne de séparation visible entre la zone de jeu et la zone interdite
    pygame.draw.line(ecran, (255,255, 255), (ZONE_JEU_LARGEUR, 0), (ZONE_JEU_LARGEUR, HAUTEUR), 3)

    # Dessiner le carré
    pygame.draw.rect(ecran, (255, 255, 255), (x, y, TAILLE_CARRE, TAILLE_CARRE))

    # Rafraîchir l’affichage
    pygame.display.flip()

pygame.quit()
