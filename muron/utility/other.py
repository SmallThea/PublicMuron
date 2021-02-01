def apply_luck(weighted_dict, luck):
    """Given a weighted dict and a luck return the same dict with weighted modified based on the luck value"""
    total = sum([val for val in weighted_dict.values()])

    for key, value in weighted_dict.copy().items():
        ratio = value/total
        weighted_dict[key] = value + (1-ratio)*(luck*0.00001*total)

def merge(l1, l2):
    """Add to l1 all the element from l2 and return l1, don't duplicate values"""
    for e2 in l2:
        if e2 not in l1:
            l1.append(e2)
    return l1

# def test():
#     luck = 200
#     weighted_dict = {
#         'fishing_0':50000,
#         'fishing_1':10000,
#         'fishing_2':2500,
#         'fishing_3':625,
#         'fishing_4':156.25,
#         'fishing_5':39.06,
#         'fishing_6': 9.77,
#     }

#     print("before")
#     for k, v in weighted_dict.items():
#         print(f"{k} : {v}")
#     print("\n---------------\n")
#     apply_luck(weighted_dict, luck)
#     print("after")
#     for k, v in weighted_dict.items():
#         print(f"{k} : {v}")

# test()