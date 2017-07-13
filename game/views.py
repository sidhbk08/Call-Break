from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.views import login as contrib_login, logout as contrib_logout
from django.shortcuts import render, redirect

from game.models import Profile, Onuser, team, cardon, player, sets, card
from django.contrib.auth.models import User
import random
import decimal
car=[]
for i in range(0,52):
	car.append(i)
random.shuffle(car)

from .forms import SignUpForm
from django.template import loader
from django.http import HttpResponse, JsonResponse
from django.conf import settings


def custom_login(request, **kwargs):
    if request.user.is_authenticated():
        return redirect(settings.LOGIN_REDIRECT_URL)
    else:
        return contrib_login(request, **kwargs)

@login_required
def custom_logout(request, **kwargs):
	myuser=request.user
	if Onuser.objects.filter(user=myuser).exists():
		Onuser.objects.filter(user=myuser).delete()
		if player.objects.filter(player__user=myuser):
			return redirect('plus_minus')
	return contrib_logout(request, **kwargs)

def signup(request):
	if request.user.is_authenticated():
		return redirect('home')
	else:
		if request.method == 'POST':
			form = SignUpForm(request.POST)
			if form.is_valid():
				user = form.save()
				user.refresh_from_db()  # load the profile instance created by the signal
				user.profile.birth_date = form.cleaned_data.get('birth_date')

				user.save()
				raw_password = form.cleaned_data.get('password1')
				user = authenticate(username=user.username, password=raw_password)
				login(request, user)
				return redirect('home')
		else:
			form = SignUpForm()
		return render(request, 'signup.html', {'form': form})

def validate_username(request):
	username = request.GET.get('username', None)
	if username==None:
		data = {
			'is_taken' : False
		}
	else:
		data = {
			'is_taken': User.objects.filter(username=username).exists()
		}
	return JsonResponse(data)

def rules(request):
	myuser=request.user
	if Onuser.objects.filter(user=myuser).exists():
		return redirect('plus_minus')
	else:
		return render(request, 'rules.html')

def highscore(request):
	myuser=request.user
	if Onuser.objects.filter(user=myuser).exists():
		return redirect('plus_minus')
	else:
		hslist = Profile.objects.filter().order_by('-rating')[:]
		template = loader.get_template('high.html')
		context = {
			'hslist': hslist,
		}
		return HttpResponse(template.render(context, request))

@login_required
def home(request):
	myuser=request.user
	if Onuser.objects.filter(user=myuser).exists():
		return redirect('plus_minus')
	else:
		return render(request, 'home.html')

@login_required
def gooff(request):
	myuser=request.user
	onlus=False
	ver=10
	if Onuser.objects.filter(user=myuser, online=False).exists:
		onlus=True
		ver=5
	if player.objects.filter(player__user=myuser).exists()==True:
		teamstatus=player.objects.filter(player__user=myuser)[0].team.status
		if 12<teamstatus<69:
			guiltyuser=Profile.objects.get(user=myuser)
			y=90
			if onlus:
				y=95
			guiltyuser.rating=(guiltyuser.rating*y)/100;
			guiltyuser.save()
		if teamstatus<69:
			myteam=player.objects.filter(player__user=myuser)[0].team
			finalplayer=player.objects.filter(team=myteam)
			ratescore=[]
			for i in range(0,4):
				ratescore.append(finalplayer[i].score)
			if ratescore!=[0,0,0,0]:
				ratescore=sorted(ratescore)
				x=1
				i=1
				for i in range(1,4):
					if ratescore[-i]==ratescore[-i-1]:
						x=x+1
					else:
						for j in range(0,x):
							finalonuser=finalplayer.filter(score=ratescore[-i])[j].player
							if (onlus and finalonuser.online==False) or onlus==False:
								finaluserrating=Profile.objects.get(user=finalonuser.user)
								finaluserrating.rating=(finaluserrating.rating*(100-ver)+ver*5*decimal.Decimal(9+x-2*i)/8)/10
								finaluserrating.save()
						x=1
				for j in range(0,x):
					i=i+1
					finalonuser=finalplayer.filter(score=ratescore[0])[j].player
					if (onlus and finalonuser.online==False) or onlus==False:
						finaluserrating=Profile.objects.get(user=finalonuser.user)
						finaluserrating.rating=(finaluserrating.rating*(100-ver)+ver*5*decimal.Decimal(9+x-2*i)/8)/10
						finaluserrating.save()
			myteam.status=69
			myteam.save()
			if onlus:
				myteam.carddistibutor=Onuser.objects.get(user=myuser, online=False)
				myteam.save()
			else:
				myteam.carddistibutor=Onuser.objects.get(user=myuser)
				myteam.save()
			for nextplayer in player.objects.filter(team=myteam):
				nextplayer.state=True
				nextplayer.save()
			return render(request, 'game.html')
		elif teamstatus==69:
			Onuser.objects.filter(user=myuser).delete()
			return redirect('home')
	elif Onuser.objects.filter(user=myuser).exists():
		Onuser.objects.filter(user=myuser).delete()
		return redirect('home')
	else:
		return redirect('home')


@login_required
def start_game(request):
	myuser=request.user
	if Onuser.objects.filter(user=myuser).exists():
		if Onuser.objects.get(user=myuser).online==True:
			if Onuser.objects.filter(ingame=False).count() < 4:
				template = loader.get_template('plus_minus.html')
				x=4-Onuser.objects.filter(ingame=False).count()
				context = {
					'list': x,
				}
				return HttpResponse(template.render(context, request))
			else:
				turn=[1,2,3,4]
				random.shuffle(turn)
				newteam=team()
				newteam.save()
				x=Onuser.objects.filter(ingame=False).last()
				for i in range(0,4):
					x.ingame=True
					x.save()
					player(team=newteam, player=x, turn=turn[i], state=True).save()
					x=Onuser.objects.filter(ingame=False).first()
				distriplayer=player.objects.get(team=newteam, turn=4)
				distriplayer.state=True
				distriplayer.save()
				return render(request,'game.html')
		else:
			return None
	else:
		return redirect('home')

@login_required
def custom_team(request):
	myuser=request.user
	if Onuser.objects.filter(user=myuser).exists():
		if player.objects.filter(player__user=myuser).exists()==False and Onuser.objects.filter(user=myuser).online==False:
			teamlist=[]
			for empty_team in team.objects.filter(status__gte=100):
				teamlist.append([empty_team.carddistibutor, empty_team.call_amount])
			data = { 'list' : teamlist }
			return JsonResponse(data)
		else:
			return redirect(plus_minus)
	else:
		return redirect('home')

@login_required
def plus_minus(request):
	myuser=request.user
	if Onuser.objects.filter(user=myuser).exists():
		if Onuser.objects.filter(user=myuser)[0].ingame==True:
			if player.objects.filter(player__user=myuser).exists():
				if player.objects.filter(player__user=myuser)[0].team.status==69:
					Onuser.objects.filter(user=myuser).delete()
					return redirect('home')
				else:
					return render(request,'game.html')
			else:
				Onuser.objects.get(user=myuser).delete()
				return redirect('home')
		else:
			return start_game(request)
	else:
		y=request.GET.get("name")
		if y!="true" and y!="false":
			return redirect('home')
		else:
			if team.objects.filter(carddistibutor__user=myuser).exists():
				team.objects.filter(carddistibutor__user=myuser).delete()
			if y=="true":
				Onuser(user=myuser).save()
				data={'values' : 1}
			else:
				turn=[1,2,3,4]
				random.shuffle(turn)
				newteam=team()
				newteam.save()
				x=Onuser(user=myuser, ingame=True, online=False)
				x.save()
				player(team=newteam, player=x, turn=turn[3], state=True).save()
				for i in range(0,3):
					x=Onuser(user=myuser, ingame=True)
					x.save()
					player(team=newteam, player=x, turn=turn[i], state=True).save()
				distriplayer=player.objects.get(team=newteam, turn=4)
				distriplayer.state=True
				distriplayer.save()
				data = {'values' : 1}
			return JsonResponse(data)

@login_required
def bhagu(request):
	myuser=request.user
	Onuser.objects.get(user=myuser).delete()
	return 0

@login_required
def waitreq(request):
	myuser=request.user
	if Onuser.objects.filter(user=myuser).exists():
		if Onuser.objects.get(user=myuser).ingame==True:
			data = {'list': 0}
			return JsonResponse(data)
		elif Onuser.objects.get(user=myuser).online==True:
			data = {'list': 4-Onuser.objects.filter(ingame=False, online=True).count()}
			return JsonResponse(data)
		else:
			data = {'list': 0}
			return JsonResponse(data)
	else:
		return redirect('home')

@login_required
def myturn(request):
	from game.models import card
	myuser = request.user
	change = request.GET.get('change')
	myuser = request.user
	myonuser = None
	trumpuser = 0
	if Onuser.objects.filter(user=myuser, online=False).exists():
		trumpuser = 1
		myonuser = Onuser.objects.get(user=myuser, online=False)
	else:
		myonuser = Onuser.objects.get(user=myuser)
	if (player.objects.get(player=myonuser).state or int(change)):
		play=player.objects.get(player=myonuser)
		play.state=False
		play.save()
		myteam=player.objects.get(player=myonuser).team
		status=myteam.status
		turn=player.objects.get(player=myonuser).turn
		myteam=player.objects.get(player=myonuser).team
		turnli=player.objects.filter(team=myteam).order_by('id')
		turnlist=[]
		callscore=[]
		name=""
		last=myteam.call_player
		y=sets.objects.filter(player__player=myonuser).count()
		for i in range(0,4):
			turnlist.append([turnli[i].player.user.username+name,turnli[i].score,turnli[i].turn])
			callscore.append([])
			steps=sets.objects.filter(player=turnli[i])
			for j in range(0,y):
				callscore[i].append(steps[j].final_sc)
			if myonuser.online==False:
				name=str(i+1)
			if last!=None:
				if last==turnli[i].player:
					last=last.user.username+str(i)
			else:
				last=0
		if status==0:
			data = {'change' : 1, 'trumpuser' : trumpuser, 'status' : status, 'turn' : turn, 'turnlist' : turnlist, 'callscore' : callscore}
		elif 1<=status<=4:
			cards=[]
			allmycard=card.objects.filter(player__player=myonuser)[:5]
			for cardis in allmycard:
				cards.append(cardis.card)
			c_call = call = myteam.call_amount
			call=call+1
			data = {'change' : 1, 'trumpuser' : trumpuser, 'status' : status, 'turn' : turn, 'card' : cards, 'call' : call, 'last' : last, 'c_call' : c_call, 'turnlist' : turnlist, 'callscore' : callscore}
			if status==1:
				call_card=myteam.call_card
				data.update({'call_card' : call_card})
		elif 5<=status<=8:
			cards=[]
			for cardis in card.objects.filter(player__player=myonuser).order_by('card'):
				cards.append(cardis.card)
			c_call = call = myteam.call_amount
			call = call+1
			if call<10:
				call=10
			data = {'change' : 1, 'trumpuser' : trumpuser, 'status' : status, 'turn' : turn, 'card' : cards, 'call' : call, 'last' : last, 'c_call' : c_call, 'turnlist' : turnlist, 'callscore' : callscore}
			if status==5:
				call_card=myteam.call_card
				data.update({'call_card' : call_card})
		elif 9<=status<=12:
			cards=[]
			for cardis in card.objects.filter(player__player=myonuser).order_by('card'):
				cards.append(cardis.card)
			c_call = myteam.call_amount
			m_score=sets.objects.filter(player__player=myonuser).last().final_sc
			call_card=myteam.call_card
			data = {'change' : 1, 'trumpuser' : trumpuser, 'status' : status, 'turn' : turn, 'card' : cards, 'c_call' : c_call, 'last' : last, 'callscore' : callscore, 'm_score' : m_score, 'turnlist' : turnlist, 'call_card': call_card}
		elif 12<status<=64:
			cards=[]
			for car in card.objects.filter(player__player=myonuser).order_by('card'):
				cards.append(car.card)
			c_call = myteam.call_amount
			candid=player.objects.filter(team=myteam)
			y=sets.objects.filter(player__player=myonuser).count()
			m_score=sets.objects.filter(player__player=myonuser).last().final_sc
			call_card=myteam.call_card
			cardison=[]
			for car in cardon.objects.filter(team=myteam):
				cardison.append(car.cardon)
			activecard=[]
			for car in card.objects.filter(player__player__user=request.user, active=True):
				activecard.append(car.card)
			data = {'change' : 1, 'trumpuser' : trumpuser, 'status' : status, 'turn' : turn, 'card' : cards, 'c_call' : c_call, 'last' : last, 'callscore' : callscore, 'm_score' : m_score, 'turnlist' : turnlist, 'cardison' : cardison, 'activecard' : activecard, 'call_card' : call_card}
		elif 65<=status<=68:
			candid=player.objects.filter(team=myteam)
			y=sets.objects.filter(player__player=myonuser).count()
			data = {'change' : 1, 'trumpuser' : trumpuser, 'status' : status, 'turn' : turn, 'callscore' : callscore, 'turnlist' : turnlist}
		elif status==69:
			candid=player.objects.filter(team=myteam)
			y=sets.objects.filter(player__player=myonuser).count()
			carddistibutor=myteam.carddistibutor.user.username
			data = {'change' : 1, 'trumpuser' : trumpuser, 'status' : status, 'turn' : turn, 'callscore' : callscore, 'turnlist' : turnlist, 'carddistibutor' : carddistibutor}
	else:
		data = {'change' : 0}
	return JsonResponse(data)

def cal(carlist):
	dicti={1:[], 2:[], 3:[], 4:[]}
	dicts=0
	maxi=0
	for acr in carlist:
		dicti[acr//13+1].append(acr%13)
	for i in range(1,5):
		count=0.0
		if len(dicti[i])>4:
			for j in range(1,5):
				if i==j:
					for carz in dicti[i]:
						if carz>9:
							count+=1
						elif carz>7:
							count+=.5
				else:
					for carz in dicti[i]:
						if carz>10:
							count+=1
						elif carz>8:
							count+=.25
			if count>maxi:
				maxi=count
				dicts=i
	return [maxi,dicts]

def player_call(carlist, trumpc):
	dicti={1:[], 2:[], 3:[], 4:[]}
	dicts=0
	maxi=0
	count=0.0
	for acr in carlist:
		dicti[acr//13+1].append(acr%13)
	for j in range(1,5):
		if trumpc==j:
			for carz in dicti[j]:
				if carz>9:
					count+=1
				elif carz>7:
					count+=.5
		else:
			for carz in dicti[j]:
				if carz>10:
					count+=1
				elif carz>8:
					count+=.25
	return int(count)

@login_required
def call(request):
	myuser=request.user
	myonuser = None
	callcard = 100
	if Onuser.objects.filter(user=myuser, online=False).exists():
		apnaonuser = Onuser.objects.get(user=myuser, online=False)
		apnaplayer = player.objects.get(player=apnaonuser)
		if apnaplayer.team.status==0:
			if apnaplayer.turn==4:
				myonuser=apnaonuser
			else:
				callcard=1
				myonuser=player.objects.get(team=apnaplayer.team, turn=4).player
		elif 0<apnaplayer.team.status<5:
			if apnaplayer.turn==apnaplayer.team.status:
				myonuser=apnaonuser
			else:
				myonuser=player.objects.get(team=apnaplayer.team, turn=apnaplayer.team.status).player
				carli=[]
				for acr in card.objects.filter(player__player=myonuser):
					carli.append(acr.card)
				x=cal(carli)
				if x[0]>apnaplayer.team.call_amount:
					callcard=int(x[1])
				else:
					callcard=0
		elif 4<apnaplayer.team.status<9:
			if apnaplayer.turn+4==apnaplayer.team.status:
				myonuser=apnaonuser
			else:
				myonuser=player.objects.get(team=apnaplayer.team, turn=apnaplayer.team.status-4).player
				carli=[]
				for acr in card.objects.filter(player__player=myonuser):
					carli.append(acr.card)
				x=cal(carli)
				amount_call=10
				if apnaplayer.team.call_amount>10:
					amount_call=apnaplayer.team.call_amount
				if x[0]>amount_call:
					callcard=int(x[1])
				else:
					callcard=0
		elif 8<apnaplayer.team.status<13:
			if apnaplayer.turn+8==apnaplayer.team.status:
				myonuser=apnaonuser
			else:
				myonuser=player.objects.get(team=apnaplayer.team, turn=apnaplayer.team.status-8).player
				carli=[]
				for acr in card.objects.filter(player__player=myonuser):
					if acr.card>51:
						carli.append(acr.card-52)
					else:
						carli.append(acr.card)
				x=player_call(carli,apnaplayer.team.call_card)
				if x<2:
					callcard=2
				else:
					callcard=x
		elif 12<apnaplayer.team.status<65:
			if (apnaplayer.team.status-apnaplayer.turn)%4==0:
				myonuser=apnaonuser
			else:
				myonuser=player.objects.get(team=apnaplayer.team, turn=(apnaplayer.team.status-1)%4+1).player
				carli=[]
				for acr in card.objects.filter(player__player=myonuser, active=True):
					carli.append(acr.card)
				callcard=min(carli)
		elif apnaplayer.team.status==65:
			apniteam=apnaplayer.team
			apniteam.status=68
			apniteam.save()
			myonuser=player.objects.get(team=apniteam, turn=4).player
			onlus=True
	else:
		myonuser = Onuser.objects.get(user=myuser)
	if player.objects.filter(player=myonuser).exists():
		if callcard == 100:
			callcard = request.GET.get('callcard')
			callcard = int(callcard)
		myteam = player.objects.get(player=myonuser).team
		turn = player.objects.get(player=myonuser).turn
		if myteam.status==0:
			if callcard==0:
				if player.objects.get(player=myonuser).turn==4:
					random.shuffle(car)
					data = {'call' : 'card has shuffled'}
					return JsonResponse(data)
				else:
					data = {'call' : 'apni bari mai karta rhiyo shuffle'}
					return JsonResponse(data)
			elif callcard==1:
				if player.objects.get(player=myonuser).turn==4:
					if card.objects.filter(player__player=myonuser).exists()==False:
						random.shuffle(car)
						cards=car
						for i,candidate in zip(range(0,4),player.objects.filter(team=myteam)):
							for j in range(0,13):
								card(player=candidate, card=cards[13*i+j]).save()
						myteam.status=1
						myteam.carddistibutor=myonuser
						myteam.save()
						candidate=player.objects.filter(team=myteam)
						for cd in candidate:
							cd.state=True
							cd.save()
						data = {'call' : 'card has distributed'}
					else:
						data = {'call' : 'kitni bar batega bhai'}
					return JsonResponse(data)
				else:
					data = {'call' : 'apni bari mai bandta rhiye'}
					return JsonResponse(data)
			else:
				data = {'call' : 'jitna bola hai utna kar'}
				return JsonResponse(data)
		if turn==myteam.status:
			if 0<callcard<5:
				myteam.call_amount=myteam.call_amount+1
				myteam.call_player=myonuser
				myteam.call_card=callcard
				myteam.status=myteam.status+1
				myteam.save()
				for nextplayer in player.objects.filter(team=myteam):
					nextplayer.state=True
					nextplayer.save()
				data = {'call' : 'your call is successfully applied and wait for your turn'}
			else:
				myteam.status=myteam.status+1
				myteam.save()
				for nextplayer in player.objects.filter(team=myteam):
					nextplayer.state=True
					nextplayer.save()
				data = {'call' : 'you have not applied for call and wait for your turn'}
		elif turn+4==myteam.status:
			if 0<callcard<5:
				if myteam.call_amount<10:
					myteam.call_amount=10
				else:
					myteam.call_amount=myteam.call_amount+1
				myteam.call_player=myonuser
				myteam.call_card=callcard
				myteam.status=myteam.status+1
				myteam.save()
				data = {'call' : 'your call is successfully applied and wait for your turn'}
			else:
				myteam.status=myteam.status+1
				myteam.save()
				data = {'call' : 'you have not applied for call and wait for your turn'}
			if myteam.status==9:
				candid=player.objects.filter(team=myteam)
				if myteam.call_amount>=10:
					for cards in card.objects.filter(player__team=myteam, player__turn=1):
						cards.active=True
						cards.save()
					myteam.status=13
					myteam.save()
					for candi in candid:
						if candi.player==myteam.call_player:
							newset=sets(player=candi, final_sc=myteam.call_amount)
							newset.save()
						else:
							newset=sets(player=candi, final_sc=0)
							newset.save()
					called=player.objects.get(player=myteam.call_player).turn
					for finalplayer in player.objects.filter(team=myteam).order_by('turn'):
						finalplayer.turn=(4+finalplayer.turn-called)%4+1
						finalplayer.save()
					for cards in card.objects.filter(player__team=myteam, player__turn=1):
						cards.active=True
						cards.save()
				elif myteam.call_amount>=5:
					for candi in candid:
						if candi.player==myteam.call_player:
							newset=sets(player=candi, final_sc=myteam.call_amount)
							newset.save()
						else:
							newset=sets(player=candi, final_sc=2)
							newset.save()
					called=player.objects.get(player=myteam.call_player).turn
					for finalplayer in player.objects.filter(team=myteam).order_by('turn'):
						finalplayer.turn=(4+finalplayer.turn-called)%4+1
						finalplayer.save()
				else:
					for candi in candid:
						newset=sets(player=candi, final_sc=2)
						newset.save()
				for i in card.objects.filter(player__team=myteam):
					if 13*(myteam.call_card-1)<=i.card<13*myteam.call_card:
						i.card=i.card+52
						i.save()
			for nextplayer in player.objects.filter(team=myteam):
				nextplayer.state=True
				nextplayer.save()
		elif turn+8==myteam.status:
			mycall=sets.objects.filter(player__player=myonuser).last()
			if 14>callcard>=mycall.final_sc:
				mycall.final_sc=callcard
				mycall.save()
				myteam.status=myteam.status+1
				myteam.save()
				for nextplayer in player.objects.filter(team=myteam):
					nextplayer.state=True
					nextplayer.save()
				data = {'call' : 'your call is successfully added'}
			else:
				data = {'call' : 'jyada dimaag mat laga'}
			if turn==4:
				for cards in card.objects.filter(player__team=myteam, player__turn=1):
					cards.active=True
					cards.save()
		elif (myteam.status-turn)%4==0 and myteam.status<65:
			if card.objects.filter(player__player__user=request.user, card=callcard, active=True).exists()==True:
				for cards in card.objects.filter(player__player=myonuser):
					if cards.card==callcard:
						cards.delete()
					else:
						cards.active=False
						cards.save()
				myteam.status=myteam.status+1
				myteam.save()
				if turn==1:
					cardon.objects.filter(team=myteam).delete()
				calledcard=cardon(team=myteam, cardon=callcard)
				calledcard.save()
				cardison=[]
				cardonrange=[]
				for cards in cardon.objects.filter(team=myteam):
					cardison.append(cards.cardon)
					cardonrange.append((cards.cardon)//13)
				if turn==1:
					nextcard=card.objects.filter(player__team=myteam, player__turn=2)
					if any(cardison[0]<cards.card<=((cardonrange[0]+1)*13-1) for cards in nextcard):
						for cards in nextcard:
							if cardison[0]<cards.card<=((cardonrange[0]+1)*13-1):
								cards.active=True
								cards.save()
					elif any(cardison[0]>cards.card>=(cardonrange[0]*13) for cards in nextcard):
						for cards in nextcard:
							if cardison[0]>cards.card>=(cardonrange[0]*13):
								cards.active=True
								cards.save()
					elif cardison[0]>=52:
						for cards in nextcard:
							cards.active=True
							cards.save()
					elif any(cards.card>=52 for cards in nextcard):
						for cards in nextcard:
							if cards.card>=52:
								cards.active=True
								cards.save()
					else:
						for cards in nextcard:
							cards.active=True
							cards.save()
					data = {'call' : 'your card is successfully applied'}
				elif turn==2:
					nextcard=card.objects.filter(player__team=myteam, player__turn=3)
					if any(cardonrange[0]*13<=cards.card<=((cardonrange[0]+1)*13-1) for cards in nextcard):
						eqn=cardison[0]
						if cardison[1]//13==cardison[0]//13 and cardison[1]>cardison[0]:
							eqn=cardison[1]
						if any(eqn<cards.card<=((cardonrange[0]+1)*13-1) for cards in nextcard)==False or (cardison[1]>=52 and cardison[0]<52):
							eqn=cardonrange[0]*13
						for cards in nextcard:
							if eqn<=cards.card<=((cardonrange[0]+1)*13-1):
								cards.active=True
								cards.save()
					elif cardison[0]>=52:
						for cards in nextcard:
							cards.active=True
							cards.save()
					elif any(cards.card>=52 for cards in nextcard):
						eqn=52
						if cardison[1]>=52:
							if any(cards.card>cardison[1] for cards in nextcard):
								eqn=cardison[1]
							else:
								eqn=0
						for cards in nextcard:
							if cards.card>=eqn:
								cards.active=True
								cards.save()
					else:
						for cards in nextcard:
							cards.active=True
							cards.save()
					data = {'call' : 'your card is successfully applied'}
				elif turn==3:
					nextcard=card.objects.filter(player__team=myteam, player__turn=4)
					if any(cardonrange[0]*13<=cards.card<=((cardonrange[0]+1)*13-1) for cards in nextcard):
						eqn=cardison[0]
						if cardison[1]//13==cardison[0]//13:
							eqn=max(cardison[0],cardison[1])
						if cardison[1]//13==cardison[2]//13:
							eqn=max(eqn,cardison[2])
						if any(eqn<cards.card<=((cardonrange[0]+1)*13-1) for cards in nextcard)==False or (cardison[0]<52 and (cardison[1]>=52 or cardison[2]>=52)):
							eqn=cardonrange[0]*13
						for cards in nextcard:
							if eqn<=cards.card<=((cardonrange[0]+1)*13-1):
								cards.active=True
								cards.save()
					elif cardison[0]>=52:
						for cards in nextcard:
							cards.active=True
							cards.save()
					elif any(cards.card>=52 for cards in nextcard):
						eqn=52
						if cardison[1]>=52 or cardison[2]>=52:
							eq=max(cardison)
							if any(cards.card>eq for cards in nextcard):
								eqn=eq
							else:
								eqn=0
						for cards in nextcard:
							if cards.card>=eqn:
								cards.active=True
								cards.save()
					else:
						for cards in nextcard:
							cards.active=True
							cards.save()
					data = {'call' : 'your card is successfully applied'}
				elif turn==4:
					wincard=cardison[0]
					if any(cards>51 for cards in cardison):
						wincard=max(cardison)
					else:
						for cards in cardison:
							if wincard<cards<(cardonrange[0]+1)*13:
								wincard=cards
					winner=cardison.index(wincard)+1
					winplayer=player.objects.get(team=myteam, turn=winner)
					winset=sets.objects.filter(player=winplayer).last()
					winset.current_sc=winset.current_sc+1
					winset.save()
					x=winner
					y=[]
					for series in player.objects.filter(team=myteam).order_by('turn'):
						y.append(series.id)
					for i in range(1,5):
						aftplay=player.objects.get(team=myteam, id=y[x-1])
						aftplay.turn=i
						aftplay.save()
						if x==4:
							x=1
						else:
							x=x+1
					for cards in card.objects.filter(player__turn=1):
						cards.active=True
						cards.save()
					data = {'call' : 'your card is successfully applied'}
				if myteam.status==65:
					finalset=sets.objects.filter(player__team=myteam)
					y=player.objects.get(player__user=myteam.carddistibutor).turn
					for finalplayer in player.objects.filter(team=myteam).order_by('turn'):
						fset=finalset.filter(player=finalplayer).last()
						if fset.final_sc==0:
							fset.final_sc=fset.current_sc
							fset.save()
						if fset.final_sc>fset.current_sc:
							fset.final_sc=-fset.final_sc
							fset.save()
						finalplayer.score=finalplayer.score+fset.final_sc
						finalplayer.turn=(2+finalplayer.turn-y)%4+1
						finalplayer.save()
				for nextplayer in player.objects.filter(team=myteam):
					nextplayer.state=True
					nextplayer.save()
			else:
				data = {'call' : 'jyada dimaag nhi hai to mat laga'}
		elif 65<=myteam.status<69 and (myteam.status-turn)%4==0:
			if callcard==1:
				if myteam.status==68:
					myteam.status=0
					myteam.call_card=1
					myteam.call_amount=4
					myteam.call_player=None
					myteam.save()
					data = {'call' : 'all players are ready your game will start shortly'}
				else:
					myteam.status=myteam.status+1
					myteam.save()
					data = {'call' : 'so you wants more game but wait for others'}
				for nextplayer in player.objects.filter(team=myteam):
					nextplayer.state=True
					nextplayer.save()
			elif callcard==0:
				ver=10
				if onlus==True:
					ver=5
				finalplayer=player.objects.filter(team=myteam)
				ratescore=[]
				for i in range(0,4):
					ratescore.append(finalplayer[i].score)
				if ratescore!=[0,0,0,0]:
					ratescore=sorted(ratescore)
					x=1
					i=1
					for i in range(1,4):
						if ratescore[-i]==ratescore[-i-1]:
							x=x+1
						else:
							for j in range(0,x):
								finalonuser=finalplayer.filter(score=ratescore[-i])[j].player
								if (onlus and finalonuser.online==False) or onlus==False:
									finaluserrating=Profile.objects.get(user=finalonuser.user)
									finaluserrating.rating=(finaluserrating.rating*(100-ver)+ver*5*decimal.Decimal(9+x-2*i)/8)/100
									finaluserrating.save()
							x=1
					for j in range(0,x):
						i=i+1
						finalonuser=finalplayer.filter(score=ratescore[0])[j].player
						if (onlus and finalonuser.online==False) or onlus==False:
							finaluserrating=Profile.objects.get(user=finalonuser.user)
							finaluserrating.rating=(finaluserrating.rating*(100-ver)+ver*5*decimal.Decimal(9+x-2*i)/8)/100
							finaluserrating.save()
				myteam.status=69
				myteam.carddistibutor=myonuser
				data = {'call' : 'you refused to play the game more'}
				for nextplayer in player.objects.filter(team=myteam):
					nextplayer.state=True
					nextplayer.save()
		else:
			data = {'call' : 'shanti rakh thoda'}
		return JsonResponse(data)
	else:
		return redirect('home')