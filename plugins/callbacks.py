import os
import ast

from pyrogram import Client as trojanz
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

if bool(os.environ.get("WEBHOOK", False)):
    from sample_config import Config
else:
    from config import Config

from script import Script
from database.filters_mdb import del_all, find_filter

from database.connections_mdb import(
    all_connections,
    active_connection,
    if_active,
    delete_connection,
    make_active,
    make_inactive
)


@trojanz.on_callback_query()
async def cb_handler(client, query):

    if query.data == "start_data":
        await query.answer()
        keyboard = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton("Aide sur les commandes", callback_data="help_data")
                ]
            ]
        )

        await query.message.edit_text(
            Script.START_MSG.format(query.from_user.mention),
            reply_markup=keyboard,
            disable_web_page_preview=True
        )
        return

    elif query.data == "help_data":
        await query.answer()
        keyboard = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton("Rejoignez-nous?", url="https://t.me/Sharing_Club"),
                    InlineKeyboardButton("À propos de moi", callback_data="about_data")
                ],
                [
                    InlineKeyboardButton("Katnice Canal", url="https://t.me/Sharing_Club"),
                    InlineKeyboardButton("Support Group", url="https://t.me/Shar_Group")
                ]
            ]
        )

        await query.message.edit_text(
            Script.HELP_MSG,
            reply_markup=keyboard,
            disable_web_page_preview=True
        )
        return

    elif query.data == "about_data":
        await query.answer()
        keyboard = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        "SOURCE CODE", url="https://t.me/SharingClub_bot")
                ],
                [
                    InlineKeyboardButton("Retour", callback_data="help_data"),
                    InlineKeyboardButton("Fermer", callback_data="close_data"),
                ]                
            ]
        )

        await query.message.edit_text(
            Script.ABOUT_MSG,
            reply_markup=keyboard,
            disable_web_page_preview=True
        )
        return

    elif query.data == "close_data":
        await query.message.delete()
        

    elif query.data == "delallconfirm":
        userid = query.from_user.id
        chat_type = query.message.chat.type

        if chat_type == "private":
            grpid  = await active_connection(str(userid))
            if grpid is not None:
                grp_id = grpid
                try:
                    chat = await client.get_chat(grpid)
                    title = chat.title
                except:
                    await query.message.edit_text("Assurez-vous que je suis présente dans votre groupe!!", quote=True)
                    return
            else:
                await query.message.edit_text(
                    "Je ne suis connecté à aucun groupe!\nVérifier /connexions ou se connecter à n'importe quel groupe",
                    quote=True
                )
                return

        elif (chat_type == "group") or (chat_type == "supergroup"):
            grp_id = query.message.chat.id
            title = query.message.chat.title

        else:
            return

        st = await client.get_chat_member(grp_id, userid)
        if (st.status == "creator") or (str(userid) in Config.AUTH_USERS):    
            await del_all(query.message, grp_id, title)
        else:
            await query.answer("Vous devez être le propriétaire du groupe ou un utilisateur autorisé pour le faire!",show_alert=True)
    
    elif query.data == "delallcancel":
        userid = query.from_user.id
        chat_type = query.message.chat.type
        
        if chat_type == "private":
            await query.message.reply_to_message.delete()
            await query.message.delete()

        elif (chat_type == "group") or (chat_type == "supergroup"):
            grp_id = query.message.chat.id
            st = await client.get_chat_member(grp_id, userid)
            if (st.status == "creator") or (str(userid) in Config.AUTH_USERS):
                await query.message.delete()
                try:
                    await query.message.reply_to_message.delete()
                except:
                    pass
            else:
                await query.answer("Ce n'est pas pour toi!!",show_alert=True)


    elif "groupcb" in query.data:
        await query.answer()

        group_id = query.data.split(":")[1]
        title = query.data.split(":")[2]
        act = query.data.split(":")[3]
        user_id = query.from_user.id

        if act == "":
            stat = "CONNECT"
            cb = "connectcb"
        else:
            stat = "DISCONNECT"
            cb = "disconnect"

        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton(f"{stat}", callback_data=f"{cb}:{group_id}:{title}"),
                InlineKeyboardButton("SUPPRIMER", callback_data=f"deletecb:{group_id}")],
            [InlineKeyboardButton("RETOUR", callback_data="backcb")]
        ])

        await query.message.edit_text(
            f"Group Name : **{title}**\nGroup ID : `{group_id}`",
            reply_markup=keyboard,
            parse_mode="md"
        )
        return

    elif "connectcb" in query.data:
        await query.answer()

        group_id = query.data.split(":")[1]
        title = query.data.split(":")[2]
        user_id = query.from_user.id

        mkact = await make_active(str(user_id), str(group_id))

        if mkact:
            await query.message.edit_text(
                f"Connecté à **{title}**",
                parse_mode="md"
            )
            return
        else:
            await query.message.edit_text(
                f"Une erreur s'est produite!!",
                parse_mode="md"
            )
            return

    elif "disconnect" in query.data:
        await query.answer()

        title = query.data.split(":")[2]
        user_id = query.from_user.id

        mkinact = await make_inactive(str(user_id))

        if mkinact:
            await query.message.edit_text(
                f"Déconnecté de **{title}**",
                parse_mode="md"
            )
            return
        else:
            await query.message.edit_text(
                f"Une erreur s'est produite!!",
                parse_mode="md"
            )
            return
    elif "deletecb" in query.data:
        await query.answer()

        user_id = query.from_user.id
        group_id = query.data.split(":")[1]

        delcon = await delete_connection(str(user_id), str(group_id))

        if delcon:
            await query.message.edit_text(
                "Successfully deleted connection"
            )
            return
        else:
            await query.message.edit_text(
                f"Some error occured!!",
                parse_mode="md"
            )
            return
    
    elif query.data == "backcb":
        await query.answer()

        userid = query.from_user.id

        groupids = await all_connections(str(userid))
        if groupids is None:
            await query.message.edit_text(
                "There are no active connections!! Connect to some groups first.",
            )
            return
        buttons = []
        for groupid in groupids:
            try:
                ttl = await client.get_chat(int(groupid))
                title = ttl.title
                active = await if_active(str(userid), str(groupid))
                if active:
                    act = " - ACTIVE"
                else:
                    act = ""
                buttons.append(
                    [
                        InlineKeyboardButton(
                            text=f"{title}{act}", callback_data=f"groupcb:{groupid}:{title}:{act}"
                        )
                    ]
                )
            except:
                pass
        if buttons:
            await query.message.edit_text(
                "Your connected group details ;\n\n",
                reply_markup=InlineKeyboardMarkup(buttons)
            )

    elif "alertmessage" in query.data:
        grp_id = query.message.chat.id
        i = query.data.split(":")[1]
        keyword = query.data.split(":")[2]
        reply_text, btn, alerts, fileid = await find_filter(grp_id, keyword)
        if alerts is not None:
            alerts = ast.literal_eval(alerts)
            alert = alerts[int(i)]
            alert = alert.replace("\\n", "\n").replace("\\t", "\t")
            await query.answer(alert,show_alert=True)
