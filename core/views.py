from django.shortcuts import render, redirect
from django.http import HttpResponse, JsonResponse, HttpResponseRedirect
from django.template import loader
from django.urls import reverse
from django.conf import settings

from datetime import datetime
from django.contrib import messages

from django.conf import settings
from core.forms import ContactoForm, UserRegistrationForm, ProductoForm, CarritoDeComprasForm, AddToCartForm
from core.models import PersonaModel, ProductoModel, Carrito_de_ComprasModel, Product, Cart, CartItem
from django.shortcuts import get_object_or_404
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
import json

from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import Group
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm

from decimal import Decimal
# Create your views here.


################ Lógica de Negocios de las paginas "comunes" ###################


def index(request):
    template = loader.get_template('core/index.html')
    return HttpResponse(template.render())

def productos(request):
    template = loader.get_template('core/productos.html')
    return HttpResponse(template.render())

def servicios(request):
    template = loader.get_template('core/servicios.html')
    return HttpResponse(template.render())


############## Lógica de Negocios de la pagina de 'contacto' que tiene un formulario que se envía a una base de datos #################


def contacto(request):
    if request.method == 'POST':
        #print(request.POST)
        contactoform = ContactoForm(request.POST)
        if contactoform.is_valid():
            contactoform.save()
            messages.success(request, '¡¡¡Formulario enviado exitosamente!!!')
            return redirect('contacto')
        else:
            # Agregar los mensajes de error al formulario
            for field, errors in contactoform.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
            #print(contactoform.errors)
    else:
        contactoform = ContactoForm()

    return render(request, 'core/contacto.html', {'contactoform': contactoform})



################ Lógica de Negocios de las paginas relativas al inicio de sesión y la creacion de usuarios ###################



def crear_usuario(request):
    if request.method == 'POST':
        #print(request.POST)
        form = UserRegistrationForm(request.POST)

        if form.is_valid():
            user = form.save(commit=False)
            user.first_name = form.cleaned_data['nombre_form']
            user.last_name = form.cleaned_data['apellido_form']
            user.save()

            persona = PersonaModel(
                user=user,
                nombre=form.cleaned_data['nombre_form'],
                apellido=form.cleaned_data['apellido_form'],
                edad=form.cleaned_data['edad'],
                email=form.cleaned_data['email'],
                dni=form.cleaned_data['dni'],
                fecha_de_nacimiento=form.cleaned_data['fecha_de_nacimiento'],
                direccion_particular=form.cleaned_data['direccion_particular'],
                ciudad=form.cleaned_data['ciudad'],
                codigo_postal=form.cleaned_data['codigo_postal'],
                telefono=form.cleaned_data['telefono'],
                CUIT=form.cleaned_data['CUIT']
            )
            persona.save()
            login(request, user)
            messages.success(request, 'Usuario creado exitosamente.')
            #print('Usuario creado exitosamente.')
            return redirect('iniciar_sesion')  # Cambia 'iniciar_sesion' por la URL de la página de inicio de sesión de tu aplicación

        else:
            messages.error(request, 'Error al crear el usuario. Revise los campos.')
            #print('Error al crear el usuario. Revise los campos.')
            #print(form.errors)

    else:
        form = UserRegistrationForm()
    return render(request, 'core/crear_usuario.html', {'form': form})

def iniciar_sesion(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            nxt = request.GET.get("next", None)
            
            if nxt is not None and nxt == 'cart_gallery':
                return redirect('cart_gallery')
            else:
                return redirect('productos')
        else:
            messages.error(request, 'Cuenta o contraseña incorrecta, inicie sesión correctamente')
    return render(request, 'core/iniciar_sesion.html', {'title': 'Iniciar sesión'})

def cerrar_sesion(request):
    logout(request)
    return redirect('index')



################ Lógica de Negocios de las paginas relativas al CRUD de los productos que ofrece la veterinaria ###################



def registrar_producto(request):
    if request.method == 'POST':
        #print(request.POST)
        #print(request.FILES)  # Imprime los archivos subidos en la consola
        form = ProductoForm(request.POST, request.FILES) # Asegúrate de agregar request.FILES para procesar los archivos subidos
        if form.is_valid():
            producto = form.save(commit=False)
            producto.save()
            #print("Archivos subidos:", request.FILES)  # Imprime los archivos subidos en la consola
            return redirect('index')
        #else:
            #print("Errores en el formulario:", form.errors)  # Imprime los errores del formulario en la consola
    else:
        form = ProductoForm()

    return render(request, 'core/registrar_producto.html', {'registrar_producto': form})

def ver_producto(request):
    tipos_de_producto = ProductoModel.objects.values_list('tipo_de_producto', flat=True).distinct()
    marcas = ProductoModel.objects.values_list('marca', flat=True).distinct()
    
    tipo_de_producto = request.GET.get('tipo_de_producto') # Obtener el valor del filtro 'tipo_de_producto' de la URL
    marca = request.GET.get('marca') # Obtener el valor del filtro 'marca' de la URL
    
    productos = ProductoModel.objects.all()
    # Aplicar los filtros si se proporcionan valores válidos
    if tipo_de_producto:
        productos = productos.filter(tipo_de_producto=tipo_de_producto)
    
    if marca:
        productos = productos.filter(marca=marca)
    
    return render(request, 'core/ver_producto.html', {'marcas': marcas,'tipos_de_producto': tipos_de_producto, 'productos': productos})

def editar_producto(request, id_producto):
    producto = get_object_or_404(ProductoModel, pk=id_producto)
    
    if request.method == 'POST':
        form = ProductoForm(request.POST, request.FILES, instance=producto)
        if form.is_valid():
            form.save()
            messages.success(request, 'Se ha editado el producto correctamente')
            return redirect('ver_producto')
    else:
        form = ProductoForm(instance=producto)
    
    return render(request, 'core/editar_producto.html', {'formulario': form})

def eliminar_producto(request, id_producto):
    try:
        producto = ProductoModel.objects.get(pk=id_producto)
    except ProductoModel.DoesNotExist:
        return render(request, 'core/404_admin.html')
    
    messages.success(request, 'Se ha eliminado el producto correctamente')          
    producto.delete()
    
    return redirect('ver_producto')

################ Lógica de Negocios de la creación del "carrito de compras"  ###################
################ En desarrollo  ###################

@login_required
def crear_carrito_de_compras(request):
    if request.method == 'POST':
        producto_id = request.POST.get('producto')
        cantidad = request.POST.get('cantidad')

        # Obtener el usuario actual
        usuario = request.user

        # Obtener la persona asociada al usuario autenticado
        persona = get_object_or_404(PersonaModel, user=usuario)

        # Crear el carrito de compras
        carrito = Carrito_de_ComprasModel(username=persona)
        carrito.save()

        if int(cantidad) > 0:
            producto = ProductoModel.objects.get(id_producto=producto_id)
            detalle = Carrito_de_ComprasModel(id_producto=producto, username=persona, cantidad_producto=cantidad)
            detalle.save()
            print(f"Producto '{producto}' agregado al carrito con cantidad '{cantidad}'.")

        return redirect('crear_carrito_de_compras')
    else:
        productos = ProductoModel.objects.all()
        return render(request, 'core/crear_carrito_de_compras.html', {'productos': productos})




@login_required
def cart_gallery(request):
    products = Product.objects.all()
    
    if request.user.is_authenticated:
        cart, created = Cart.objects.get_or_create(user=request.user, completed=False)
        
    context = {"products":products, "cart": cart}
    return render(request, "core/cart_gallery.html", context)

@login_required
def cart(request):
    
    cart = None
    cartitems = []
    cart_items = CartItem.objects.filter(user=request.user)
    
    # Calculate the total price for each cart item
    for cart_item in cart_items:
        cart_item.total_price = cart_item.id_producto.precio_de_venta * cart_item.cantidad_producto
    
    if request.user.is_authenticated:
        cart, created = Cart.objects.get_or_create(user=request.user, completed=False)
        cartitems = cart.cartitems.all()
    
    context = {
        "cart":cart, 
        "items":cartitems,
        'cart_items': cart_items,
        }
    return render(request, "core/cart.html", context)


def add_to_cart(request):
    data = json.loads(request.body)
    product_id = data["id"]
    product = Product.objects.get(id=product_id)
    
    if request.user.is_authenticated:
        cart, created = Cart.objects.get_or_create(user=request.user, completed=False)
        cartitem, created =CartItem.objects.get_or_create(cart=cart, product=product)
        cartitem.quantity += 1
        cartitem.save()
        
        
        num_of_item = cart.num_of_items
        
        print(cartitem)
    return JsonResponse(num_of_item, safe=False)


def confirm_payment(request, pk):
    cart = Cart.objects.get(id=pk)
    cart.completed = True
    cart.save()
    messages.success(request, "Payment made successfully")
    return redirect("core/cart_gallery")


