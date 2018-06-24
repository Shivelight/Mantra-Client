# -*- coding: utf-8 -*-
import asyncio

from mantra.service.ttypes import ContentType

from .util.pl import plugin


@plugin()
async def me(self, msg, args):
    await self.sendContact(msg.to, self.mid)


@plugin()
async def myprofile(self, msg, args):
    if len(args) == 1:
        profile = await self.Talk.getProfile()
        groups = await self.Talk.getGroupIdsJoined()
        invitations = await self.Talk.getGroupIdsInvited()
        friends = await self.Talk.getAllContactIds()
        await self.sendText(msg.to, (
            "「 Profile 」\n"
            f"Name: {profile.displayName}\n"
            f"Groups: {len(groups)}\n"
            f"Friends: {len(friends)}\n"
            f"Invitations: {len(invitations)}\n\n"
            "・Commands\n"
            "{0} myprofile id\n"
            "{0} myprofile bio\n"
            "{0} myprofile cover\n"
            "{0} myprofile pic\n"
            "{0} myprofile vid\n"
            "{0} myprofile setbio\n"
            "{0} myprofile setcover\n"
            "{0} myprofile setpic\n"
            "{0} myprofile setvid"
        ).format(self.key.title()))
    else:
        if args[1] == "id":
            await self.sendText(msg.to, self.mid)

        elif args[1] == "cover":
            await self.sendProfileCover(msg.to, self.mid)

        elif args[1] == "pic":
            try:
                await self.sendProfileImage(msg.to, self.mid)
            except Exception:
                await self.sendText(msg.to,
                                    "「 Profile 」\nProfile video is not set.")

        elif args[1] == "bio":
            profile = await self.Talk.getProfile()
            if not profile.statusMessage:
                await self.sendText(msg.to, "「 Profile 」\nBio is not set.")
            else:
                await self.sendText(msg.to, profile.statusMessage)

        elif args[1] == "vid":
            try:
                await self.sendProfileVideo(msg.to, self.mid)
            except Exception:
                await self.sendText(msg.to,
                                    "「 Profile 」\nProfile video is not set.")

        elif args[1] == "setbio":
            try:
                if len(args[2]) > 500:
                    await self.sendText(msg.to, (
                        "「 Profile 」\n"
                        "Bio can't be longer than 500 characters."))
                else:
                    await self.Talk.updateProfileAttribute(0, 16, args[2])
                    await self.sendText(msg.to, "「 Profile 」\nBio updated.")
            except IndexError:
                await self.sendText(msg.to, (
                    "「 Profile 」\n"
                    "Usage: {} myprofile setbio <text>"
                ).format(self.key.title()))

        elif args[1] == "setcover":
            if self._state['wait']['type']:
                waiting = [f"- {ContentType._VALUES_TO_NAMES[c]}"
                           for c in self._state['wait']['type']]
                await self.sendText(msg.to, (
                    "「 Profile 」\n"
                    "Other command is still waiting for:\n{}\n\n"
                    "Use '{} abort' to cancel the other command."
                ).format('\n'.join(waiting), self.key.title()))
                return

            self._state['wait']['type'] = {1}
            await self.sendText(msg.to, (
                "「 Profile 」\n"
                "Upload an image..\n"
                "'{} abort' to cancel."
            ).format(self.key.title()))
            queue = self._state['wait']['queue']
            for _ in range(5):
                try:
                    task = await asyncio.wait_for(queue.get(), 60)
                    queue.task_done()
                except asyncio.TimeoutError:
                    if _ == 4:
                        await self.sendText(msg.to, "「 Profile 」\nTimed out.")
                        return
                    else:
                        await self.sendText(
                            msg.to, "「 Profile 」\nWaiting for image...")
                else:
                    if task is None:
                        await self.sendText(msg.to, "「 Profile 」\nAborted..")
                        return
                    self._state['wait']['type'].remove(task.contentType)
                    break

            await asyncio.sleep(1)  # Wait for the image successfully uploaded
            url = f"http://{self.OBS}/os/m/{task.id}"
            data = await self.session.get(url, headers=self.session._headers)
            if data.status_code != 200:
                await self.sendText(
                    msg.to, "「 Profile 」\nFailed to fetch image, try again.")
                return
            oid, _ = await self.Timeline.uploadProfileCover(data)
            await self.Timeline.updateProfileCoverByOid(oid)
            await self.sendText(
                msg.to, "「 Profile 」\nCover has been changed.")

        elif args[1] == "setpic":
            if self._state['wait']['type']:
                waiting = [f"- {ContentType._VALUES_TO_NAMES[c]}"
                           for c in self._state['wait']['type']]
                await self.sendText(msg.to, (
                    "「 Profile 」\n"
                    "Other command is still waiting for:\n{}\n\n"
                    "Use '{} abort' to cancel the other command."
                ).format('\n'.join(waiting), self.key.title()))
                return

            self._state['wait']['type'] = {1}
            await self.sendText(msg.to, (
                "「 Profile 」\n"
                "Upload an image..\n"
                "Note: Your profile video will be gone.\n"
                "'{} abort' to cancel."
            ).format(self.key.title()))
            queue = self._state['wait']['queue']
            for _ in range(5):
                try:
                    task = await asyncio.wait_for(queue.get(), 60)
                    queue.task_done()
                except asyncio.TimeoutError:
                    if _ == 4:
                        await self.sendText(msg.to, "「 Profile 」\nTimed out.")
                        return
                    else:
                        await self.sendText(
                            msg.to, "「 Profile 」\nWaiting for image...")
                else:
                    if task is None:
                        await self.sendText(msg.to, "「 Profile 」\nAborted..")
                        return
                    self._state['wait']['type'].remove(task.contentType)
                    break

            await asyncio.sleep(1)
            url = f"http://{self.OBS}/os/m/{task.id}"
            data = await self.session.get(url, headers=self.session._headers)
            if data.status_code != 200:
                await self.sendText(
                    msg.to, "「 Profile 」\nFailed to fetch image, try again.")
                return
            await self.changeProfilePicture(data)
            await self.sendText(
                msg.to, "「 Profile 」\nProfile picture has been changed.")

        elif args[1] == "setvid":
            if self._state['wait']['type']:
                waiting = [f"- {ContentType._VALUES_TO_NAMES[c]}"
                           for c in self._state['wait']['type']]
                await self.sendText(msg.to, (
                    "「 Profile 」\n"
                    "Other command is still waiting for:\n{}\n\n"
                    "Use '{} abort' to cancel the other command."
                ).format('\n'.join(waiting), self.key.title()))
                return

            self._state['wait']['type'] = {1, 2}
            await self.sendText(msg.to, (
                "「 Profile 」\n"
                "Upload a video and an image..\n"
                "'{} abort' to cancel."
            ).format(self.key.title()))
            queue = self._state['wait']['queue']
            for _ in range(10):
                try:
                    task = await asyncio.wait_for(queue.get(), 60)
                    queue.task_done()
                except asyncio.TimeoutError:
                    if _ == 9:
                        await self.sendText(msg.to, "「 Profile 」\nTimed out.")
                        return
                    else:
                        waiting = [ContentType._VALUES_TO_NAMES[c]
                                   for c in self._state['wait']['type']]
                        await self.sendText(msg.to, (
                            "「 Profile 」\nWaiting for {}.."
                        ).format(', '.join(waiting)))
                else:
                    if task is None:
                        await self.sendText(msg.to, "「 Profile 」\nAborted..")
                        return
                    self._state['wait']['type'].remove(task.contentType)
                    if task.contentType == 1:
                        pic = task.id
                        await self.sendText(msg.to, "Image received.")
                    elif task.contentType == 2:
                        vid = task.id
                        await self.sendText(msg.to, "Video received.")

                    if not self._state['wait']['type']:
                        break

            await asyncio.sleep(1)
            pic = f"http://{self.OBS}/os/m/{pic}"
            vid = f"http://{self.OBS}/os/m/{vid}"

            viddata = await self.session.get(vid, headers=self.session._headers)
            if viddata.status_code != 200:
                await self.sendText(
                    msg.to, "「 Profile 」\nFailed to fetch video, try again.")
                return

            picdata = await self.session.get(pic, headers=self.session._headers)
            if picdata.status_code != 200:
                await self.sendText(
                    msg.to, "「 Profile 」\nFailed to fetch image, try again.")
                return

            await self.changeProfileVideo(viddata, picdata)
            await self.sendText(
                msg.to, "「 Profile 」\nProfile video has been changed.")
