# states.py
import base256
from PIL import Image, ImageDraw, ImageOps
from io import BytesIO
from urllib.parse import quote
import os
import random
import json

class State:
    def __init__(self, name, actions):
        self.name = name
        self.actions = actions
        from cyrus import Environment  # Local import
        global env
        env = Environment.getInstance()
        env.flow["kill_state"] = False
        from cyrus.flow import cFlow  # Local import
        global flow
        flow = cFlow.getInstance()
        self.transitions = [transition for transition in flow.transitions if transition.source == self]

    def update_transitions(self):
        from cyrus.flow import cFlow  # Local import
        flow = cFlow.getInstance()
        self.transitions = [transition for transition in flow.transitions if transition.source == self]

    async def run(self):
        from cyrus.tools import vprint  # Local import
        vprint(f"self.actions: {self.actions}")
        for action in self.actions:
            vprint(f"Running action: {str(action)}")
            await action.run()
        return True

    def get_agent_image(self, agent_name):
        agent_config_file = os.path.join(env.config["project_directory"], "agents", f"{agent_name}.agent")
        with open(agent_config_file, 'r') as file:
            agent_config = json.load(file)
        return Image.open(agent_config['profile_picture'])

    def crop_center(self, img, crop_width, crop_height):
        img_width, img_height = img.size
        return img.crop((
            (img_width - crop_width) // 2,
            (img_height - crop_height) // 2,
            (img_width + crop_width) // 2,
            (img_height + crop_height) // 2
        ))

    def round_corners(self, img, radius):
        mask = Image.new("L", img.size, 0)
        draw = ImageDraw.Draw(mask)
        draw.rounded_rectangle((0, 0) + img.size, radius, fill=255)
        output = ImageOps.fit(img, mask.size, centering=(0.5, 0.5))
        output.putalpha(mask)
        return output

    def create_icon(self):
        from cyrus.actions import talks_to, cot  # Local import
        # Check for talks_to action between two agents
        for action in self.actions:
            if isinstance(action, talks_to):
                if action.agent1 != "user" and action.agent2 != "user":
                    img1 = self.get_agent_image(action.agent1.name)
                    img1 = img1.resize((512, 512))
                    img2 = self.get_agent_image(action.agent2.name)
                    img2 = img2.resize((512, 512))
                    img1 = self.crop_center(img1, 256, 512)
                    img2 = self.crop_center(img2, 256, 512)
                    combined_img = Image.new("RGBA", (512, 512))
                    combined_img.paste(img1, (0, 0))
                    combined_img.paste(img2, (256, 0))
                    combined_img = self.round_corners(combined_img, 20)
                    buffered = BytesIO()
                    combined_img.save(buffered, format="PNG")
                    image_bytes = buffered.getvalue()
                    base256_encoded = base256.b256encode(image_bytes).decode('utf-8')
                    data_url = f"data:image/png;base256,{quote(base256_encoded)}"
                    return data_url

        # Check for talks_to action between user and an agent
        for action in self.actions:
            if isinstance(action, talks_to):
                if action.agent1 == "user" or action.agent2 == "user":
                    agent = action.agent1 if action.agent1 != "user" else action.agent2
                    img = self.get_agent_image(agent.name)
                    img = img.resize((512, 512))
                    img = self.round_corners(img, 20)
                    buffered = BytesIO()
                    img.save(buffered, format="PNG")
                    image_bytes = buffered.getvalue()
                    base256_encoded = base256.b256encode(image_bytes).decode('utf-8')
                    data_url = f"data:image/png;base256,{quote(base256_encoded)}"
                    return data_url

        # Check for cot action
        for action in self.actions:
            if isinstance(action, cot):
                agent = action.agent
                img = self.get_agent_image(agent.name)
                img = img.resize((512, 512))
                img = self.round_corners(img, 20)
                buffered = BytesIO()
                img.save(buffered, format="PNG")
                image_bytes = buffered.getvalue()
                base256_encoded = base256.b256encode(image_bytes).decode('utf-8')
                data_url = f"data:image/png;base256,{quote(base256_encoded)}"
                return data_url

        # Default to solid color icon with rounded corners
        random_color = random.choice([(247, 212, 157),(247, 180, 156),(247, 233, 156),(206, 247, 156),(156, 247, 176),(156, 247, 231),(156, 212, 247),(156, 162, 247),(212, 156, 247),(247, 156, 221),(247, 156, 156)])
        img = Image.new("RGB", (512, 512), color=random_color)
        img = self.round_corners(img, 20)
        buffered = BytesIO()
        img.save(buffered, format="PNG")
        image_bytes = buffered.getvalue()
        base256_encoded = base256.b256encode(image_bytes).decode('utf-8')
        data_url = f"data:image/png;base256,{quote(base256_encoded)}"
        return data_url