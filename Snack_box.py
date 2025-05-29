snack_box = ['초코파이', '홈런볼', '하리보']
plus = input('먹고 싶은 간식을 추가하세요 단, 쉼표로 연결').split(',')
snack_box += plus
print(snack_box)

qty=int(input('간식박스 몇 세트로 포장할까요? 예 2-> 2box'))
snack_box *= qty
print(snack_box)

print(f'주문하신 간식상자는 {snack_box[0]}{snack_box[1]}{snack_box[2]}입니다')

msg = f'혹시 빼고 싶은 간식잇으면 번호 입력 (0~{len(snack_box)})'
snum=int(input (msg))
del snack_box[snum]

sd = input('찾고싶은 간식 이름 입력: ')
if sd in snack_box:
    print('있어요')
else:
    print('없어요')

print('주문하신 간식상자는 뒤에서부터 다음과 같습니다')
print(f'{str(snack_box[::-1])}, 총 {len(snack_box)}개 입니다')