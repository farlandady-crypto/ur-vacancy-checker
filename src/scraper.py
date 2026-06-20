import requests
from bs4 import BeautifulSoup
from typing import List, Dict, Tuple
from datetime import datetime
import re
from .config import HEADERS, UR_TARGETS

def fetch_rooms(target: Dict) -> Tuple[List[Dict], str]:
    """
    通过解析物件详情页HTML来获取空房列表
    """
    url = target['url']
    try:
        response = requests.get(url, headers=HEADERS, timeout=15)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 方法1：查找空房表格 - 根据实际页面结构
        # UR网站的空房信息通常在 table 中，class可能包含 "vacant" 或 "room"
        room_table = None
        
        # 尝试多种方式查找表格
        # 1) 直接查找包含空房信息的表格
        tables = soup.find_all('table')
        for table in tables:
            # 检查表格是否包含房间相关的关键词
            table_text = table.get_text()
            if any(keyword in table_text for keyword in ['間取図', '部屋名', '家賃', '床面積', '階数']):
                room_table = table
                break
        
        # 2) 如果上面没找到，尝试通过class查找
        if not room_table:
            room_table = soup.find('table', class_=re.compile(r'vacant|room|bukken'))
        
        # 3) 如果还是没找到，尝试查找包含空房信息的div
        if not room_table:
            # 查找包含空房列表的div
            room_containers = soup.find_all('div', class_=re.compile(r'room|vacant|bukken'))
            for container in room_containers:
                # 如果div内有表格，使用第一个表格
                table_in_div = container.find('table')
                if table_in_div:
                    room_table = table_in_div
                    break
        
        if not room_table:
            # 调试：打印页面标题和部分内容
            page_title = soup.find('title')
            title_text = page_title.get_text() if page_title else "未知"
            print(f"   🔍 页面标题: {title_text}")
            
            # 检查是否真的没有空房
            no_room_text = soup.find_all(string=re.compile(r'ご案内できるお部屋がございません|空室は前日以前の状況'))
            if no_room_text:
                return [], "页面显示：目前没有可立即入住的空房"
            
            return [], f"未找到空房表格，页面结构可能已变化。标题: {title_text}"
        
        # 解析表格数据
        rooms = []
        rows = room_table.find_all('tr')
        
        # 找到表头行，确定各列索引
        header_row = None
        header_cells = []
        for row in rows:
            cells = row.find_all(['th', 'td'])
            cell_texts = [cell.get_text(strip=True) for cell in cells]
            # 检查是否包含表头关键词
            if any(keyword in ' '.join(cell_texts) for keyword in ['間取図', '部屋名', '家賃']):
                header_row = row
                header_cells = cell_texts
                break
        
        # 确定各列位置
        col_indices = {
            'name': -1,
            'rent': -1,
            'type': -1,
            'floor_space': -1,
            'floor': -1,
            'status': -1
        }
        
        for i, cell_text in enumerate(header_cells):
            if '部屋名' in cell_text or 'room' in cell_text.lower():
                col_indices['name'] = i
            elif '家賃' in cell_text or '賃料' in cell_text:
                col_indices['rent'] = i
            elif '間取' in cell_text or 'type' in cell_text.lower():
                col_indices['type'] = i
            elif '床面積' in cell_text or '面積' in cell_text:
                col_indices['floor_space'] = i
            elif '階数' in cell_text or '階' in cell_text:
                col_indices['floor'] = i
            elif '状態' in cell_text or '状況' in cell_text:
                col_indices['status'] = i
        
        # 如果没找到表头，使用默认列顺序
        if col_indices['name'] == -1:
            # 根据观察到的典型UR表格结构：图 | 房名 | 家賃 | 間取 | 面積 | 階数
            col_indices = {
                'name': 1,
                'rent': 2,
                'type': 3,
                'floor_space': 4,
                'floor': 5,
                'status': 6
            }
        
        # 遍历数据行
        for row in rows:
            # 跳过表头行
            if row == header_row:
                continue
            
            cells = row.find_all('td')
            if len(cells) < 5:  # 至少要有足够的数据列
                continue
            
            # 提取房间信息
            name = cells[col_indices['name']].get_text(strip=True) if col_indices['name'] < len(cells) else '未知房号'
            rent_text = cells[col_indices['rent']].get_text(strip=True) if col_indices['rent'] < len(cells) else ''
            type_text = cells[col_indices['type']].get_text(strip=True) if col_indices['type'] < len(cells) else ''
            floor_space_text = cells[col_indices['floor_space']].get_text(strip=True) if col_indices['floor_space'] < len(cells) else ''
            floor_text = cells[col_indices['floor']].get_text(strip=True) if col_indices['floor'] < len(cells) else ''
            
            # 提取房间ID（从链接或房名中）
            room_id = None
            link = row.find('a')
            if link and link.get('href'):
                # 尝试从URL中提取ID
                id_match = re.search(r'/(\d+)_room\.html', link['href'])
                if id_match:
                    room_id = id_match.group(1)
            
            if not room_id:
                # 使用房名+物件ID组合作为唯一标识
                room_id = f"{target['params']['danchi']}_{name}"
            
            # 清理租金：提取数字
            rent_clean = rent_text
            rent_match = re.search(r'([\d,]+)円', rent_text)
            if rent_match:
                rent_clean = rent_match.group(1) + '円'
            else:
                rent_clean = rent_text or '不明'
            
            # 清理面积
            floor_space_clean = floor_space_text
            if '&#13217;' in floor_space_clean:
                floor_space_clean = floor_space_clean.replace('&#13217;', '㎡')
            
            # 从租金文本中提取共益费（如果有）
            common_fee = '不明'
            fee_match = re.search(r'\(([\d,]+)円\)', rent_text)
            if fee_match:
                common_fee = fee_match.group(1) + '円'
            
            room = {
                'id': room_id,
                'name': name,
                'rent': rent_clean,
                'common_fee': common_fee,
                'type': type_text,
                'floor_space': floor_space_clean,
                'floor': floor_text,
                'status': '常规募集',
                'url': link['href'] if link and link.get('href') else '',
                'shikikin': '不明',
                'requirement': '不明'
            }
            
            # 只添加有效的房间（至少有房名）
            if name and name not in ['', '間取図', '部屋名']:
                rooms.append(room)
        
        # 如果解析出的房间数为0，尝试从页面中直接提取文本
        if len(rooms) == 0:
            # 查找包含"号室"的文本
            room_texts = soup.find_all(string=re.compile(r'\d+号室'))
            if room_texts:
                print(f"   ⚠️ 发现可能的房间文本: {len(room_texts)} 个")
                for text in room_texts[:3]:
                    print(f"      - {text.strip()}")
                return [], "发现房间文本但无法解析表格，可能页面结构有变化"
        
        return rooms, f"发现 {len(rooms)} 套空房"
        
    except requests.exceptions.RequestException as e:
        return [], f"请求失败: {str(e)}"
    except Exception as e:
        return [], f"解析失败: {str(e)}"

def format_room_info(room: Dict) -> Dict:
    """格式化房间信息"""
    return room

def check_all_targets() -> Dict:
    """检查所有目标物件"""
    results = {}
    
    for target in UR_TARGETS:
        print(f"🔍 检查: {target['name']}")
        rooms, message = fetch_rooms(target)
        print(f"   {message}")
        
        formatted_rooms = [format_room_info(room) for room in rooms]
        
        results[target['name']] = {
            'url': target['url'],
            'rooms': formatted_rooms,
            'count': len(formatted_rooms),
            'message': message,
            'check_time': datetime.now().isoformat()
        }
    
    return results
