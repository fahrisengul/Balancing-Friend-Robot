import pygame
import time
import sys

from character_ui import PoodleCharacter
from speech_engine import PoodleSpeech
from brain.brain import PoodleBrain
from brain.orchestrator import RobotOrchestrator


def main():
    pygame.init()
    screen = pygame.display.set_mode((1024, 600))
    pygame.display.set_caption("Poodle Robot - AI Brain")
    clock = pygame.time.Clock()

    # Yeni animasyonlu karakter
    character = PoodleCharacter(1024, 600)

    brain = PoodleBrain()

    # Varsayılan mikrofon
    # İstersen sabitle:
    # speech = PoodleSpeech(input_device_index=1)
    speech = PoodleSpeech(input_device_index=0)
    speech.debug_list_input_devices()

    # Orchestrator mevcut yapıyla aynı kalıyor
    orchestrator = RobotOrchestrator(
        face=character,   # PoodleFace yerine PoodleCharacter veriyoruz
        speech=speech,
        brain=brain
    )
    orchestrator.start()

    running = True

    print("\n--- Poodle Robot Zeka Katmanıyla Aktif ---")
    print("Doğal dinleme aktif. Pencereyi kapatarak çıkabilirsin.")
    print("SPACE: demo state cycle | ESC: çıkış")

    # Demo amaçlı state gezme
    demo_states = ["idle", "attentive", "listening", "thinking", "speaking", "muted", "error"]
    demo_state_index = 0

    last_time = time.time()

    try:
        while running:
            now = time.time()
            dt = now - last_time
            last_time = now

            orchestrator.handle_pending_speech_events()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False

                    # Sprint 4.1 test kolaylığı:
                    # SPACE ile karakter state'lerini manuel gez
                    elif event.key == pygame.K_SPACE:
                        demo_state_index = (demo_state_index + 1) % len(demo_states)
                        character.set_state(demo_states[demo_state_index])
                        print(f">>> [DEMO STATE] {demo_states[demo_state_index]}")

            # Mouse bakışı karaktere ver
            mouse_pos = pygame.mouse.get_pos()
            character.update_gaze(mouse_pos[0], mouse_pos[1])

            # Karakter update + draw
            character.update(dt)
            character.draw(screen)

            pygame.display.flip()
            clock.tick(60)

    finally:
        orchestrator.stop()
        pygame.quit()
        sys.exit()


if __name__ == "__main__":
    main()
