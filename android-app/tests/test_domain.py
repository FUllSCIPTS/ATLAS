from pathlib import Path
import pytest
from atlas_go.domain import Cart, Offer, distance, fare, money
from atlas_go.store import LocalStore


def test_route_fare_and_vehicle():
    assert fare(0,1)==860
    assert fare(0,1,True)==1118
    assert fare(1,3)==1880
    assert money(490)=='€4.90'


@pytest.mark.parametrize('pickup,destination',[(0,0),(-1,1),(1,4)])
def test_invalid_route(pickup,destination):
    with pytest.raises(ValueError):
        distance(pickup,destination)


def test_shared_route_capacity():
    offer=Offer('1','A',0,1,2,490,2)
    assert offer.matches(0,1,2)
    assert not offer.matches(1,0,1)
    offer.reserve(2)
    assert not offer.matches(0,1,1)
    with pytest.raises(ValueError):
        offer.reserve(1)
    offer.release(2)
    assert offer.seats==2


def test_cart_cent_totals_and_restaurant():
    cart=Cart()
    for item in ('bowl','bowl','juice'):
        cart.add(item)
    assert cart.total()==2820
    with pytest.raises(ValueError):
        cart.add('pizza')
    assert cart.count()==3
    cart.remove('bowl')
    assert cart.total()==1730
    cart.clear()
    assert cart.total()==0
    cart.add('pizza')
    assert cart.restaurant==1


def test_quantity_limit_and_last_removal():
    cart=Cart()
    for _ in range(10):cart.add('wrap')
    with pytest.raises(ValueError):cart.add('wrap')
    for _ in range(10):cart.remove('wrap')
    assert cart.restaurant is None and cart.total()==0


def test_shared_booking_persistence_and_cancellation(tmp_path):
    store=LocalStore(tmp_path/'state.json')
    store.book(0,1,offer_id='pool-1',party=2)
    assert store.ride['fare']==980
    restored=LocalStore(store.path)
    assert restored.offers[0].seats==1
    assert restored.ride['party']==2
    with pytest.raises(ValueError):restored.book(0,1)
    restored.advance_ride(cancel=True)
    assert restored.offers[0].seats==3 and restored.ride is None
    assert restored.history[-1]['status']=='Cancelled'


def test_failed_shared_match_does_not_reserve(tmp_path):
    store=LocalStore(tmp_path/'state.json')
    with pytest.raises(ValueError):store.book(1,0,offer_id='pool-1')
    assert store.offers[0].seats==3 and store.ride is None


def test_solo_completion_and_history(tmp_path):
    store=LocalStore(tmp_path/'state.json')
    store.book(0,1)
    for _ in range(3):store.advance_ride()
    restored=LocalStore(store.path)
    assert restored.ride is None and restored.history[-1]['status']=='Completed'


def test_food_checkout_and_completion(tmp_path):
    store=LocalStore(tmp_path/'state.json')
    with pytest.raises(ValueError):store.checkout(0)
    store.cart.add('bowl');store.cart.add('juice');store.save()
    restored=LocalStore(store.path)
    assert restored.cart.total()==1730
    restored.checkout(2)
    assert not restored.cart.items and restored.order['fare']==1730
    restored.cart.add('pizza')
    with pytest.raises(ValueError):restored.checkout(0)
    assert restored.cart.count()==1
    for _ in range(3):restored.advance_order()
    assert restored.order is None and restored.history[-1]['status']=='Delivered'


def test_reset_deletes_activity_and_restores_offers(tmp_path):
    store=LocalStore(tmp_path/'state.json')
    store.book(0,1,offer_id='pool-1');store.cart.add('bowl');store.save()
    store.reset()
    restored=LocalStore(store.path)
    assert restored.ride is None and restored.order is None and not restored.history
    assert restored.cart.count()==0 and restored.offers[0].seats==3


def test_malformed_saved_state_is_preserved_and_reset(tmp_path):
    path=tmp_path/'state.json';path.write_text('broken')
    store=LocalStore(path)
    assert store.ride is None
    assert path.with_suffix('.invalid.json').read_text()=='broken'

@pytest.mark.parametrize('stage',[0,1,2])
def test_restart_preserves_each_ride_stage(tmp_path,stage):
    store=LocalStore(tmp_path/'state.json');store.book(0,1)
    for _ in range(stage):store.advance_ride()
    restored=LocalStore(store.path)
    assert restored.ride['stage']==stage
    restored.advance_ride(cancel=True);restored.advance_ride(cancel=True)
    assert len(restored.history)==1

@pytest.mark.parametrize('stage',[0,1,2])
def test_restart_preserves_each_food_stage(tmp_path,stage):
    store=LocalStore(tmp_path/'state.json');store.cart.add('pizza');store.checkout(3)
    for _ in range(stage):store.advance_order()
    assert LocalStore(store.path).order['stage']==stage

@pytest.mark.parametrize('pickup,destination',[(a,b) for a in range(4) for b in range(4) if a!=b])
def test_all_route_fares(pickup,destination):
    assert fare(pickup,destination)==fare(destination,pickup)
    assert fare(pickup,destination,True)>fare(pickup,destination)

def test_food_and_ride_independent(tmp_path):
    store=LocalStore(tmp_path/'state.json');store.book(0,1)
    store.cart.add('curry');store.checkout(2)
    assert store.ride and store.order
    store.advance_ride(cancel=True)
    assert store.order and not store.ride

def test_invalid_party_does_not_reserve(tmp_path):
    store=LocalStore(tmp_path/'state.json')
    for party in (0,3,-1):
        with pytest.raises(ValueError):store.book(0,1,offer_id='pool-2',party=party)
    assert store.ride is None and store.offers[1].seats==2

def test_structure_corruption_is_recovered(tmp_path):
    import json
    path=tmp_path/'state.json'
    path.write_text(json.dumps({'ride':{'stage':99},'cart':{},'history':[]}))
    store=LocalStore(path)
    assert store.ride is None and path.with_suffix('.invalid.json').exists()

def test_invalid_ui_does_not_break_booking(tmp_path):
    store=LocalStore(tmp_path/'state.json');store.book(0,1)
    store.ui={'screen':'unknown','pickup':99,'destination':'bad','party':9,'comfort':'yes'};store.save()
    restored=LocalStore(store.path)
    assert restored.ride and not restored.ui

def test_atomic_save_failure_preserves_previous_file(tmp_path,monkeypatch):
    store=LocalStore(tmp_path/'state.json');store.cart.add('bowl');store.save()
    before=store.path.read_bytes()
    def fail(_source,_target):raise OSError('Simulated failed rename')
    monkeypatch.setattr(Path,'replace',fail)
    store.cart.add('juice')
    with pytest.raises(OSError):store.save()
    assert store.path.read_bytes()==before

@pytest.mark.parametrize('operation',['ride','food','cart'])
def test_failed_storage_rolls_back_transaction(tmp_path,monkeypatch,operation):
    store=LocalStore(tmp_path/'state.json');store.cart.add('bowl');store.save()
    def fail():raise OSError('Storage full')
    monkeypatch.setattr(store,'save',fail)
    with pytest.raises(OSError):
        if operation=='ride':store.book(0,1,offer_id='pool-1',party=2)
        elif operation=='food':store.checkout(0)
        else:store.update_cart('add','juice')
    assert store.ride is None and store.order is None
    assert store.offers[0].seats==3 and store.cart.items=={'bowl':1}

def test_reset_removes_preserved_invalid_file(tmp_path):
    path=tmp_path/'state.json';path.write_text('broken')
    store=LocalStore(path)
    assert path.with_suffix('.invalid.json').exists()
    store.reset()
    assert not path.with_suffix('.invalid.json').exists()
