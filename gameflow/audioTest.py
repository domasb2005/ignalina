import pygame

pygame.mixer.init()
print("Available SDL audio devices:")
for i in range(pygame.mixer.get_num_devices()):
    print(f"{i}: {pygame.mixer.get_device_name(i)}")
pygame.mixer.quit()

